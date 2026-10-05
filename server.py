#!/usr/bin/env python3
"""Local practice server. Run:  python3 server.py  [--port 8000] [--no-browser]"""

import argparse
import json
import sqlite3
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import questions as Q

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
RUNNER = ROOT / "runner.py"
TIME_LIMIT = {"sample": 5, "submit": 10}
MAX_SQL_ROWS = 200

CONTENT_TYPES = {".html": "text/html", ".js": "application/javascript", ".css": "text/css",
                 ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}


# ----------------------------------------------------------------- python ---

def run_python(q, code, mode):
    tests = q["tests"] if mode == "submit" else [t for t in q["tests"] if not t.get("hidden")]
    payload = json.dumps({"code": code, "reference": q["solution"], "func": q["func"], "tests": tests})
    proc = subprocess.Popen([sys.executable, "-I", str(RUNNER)], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        out, err = proc.communicate(payload, timeout=TIME_LIMIT[mode])
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        timed_out = True

    events = []
    for line in out.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return python_feedback(q, tests, events, timed_out, err, mode)


def python_feedback(q, tests, events, timed_out, stderr, mode):
    pointers = []
    signature = next((ln.strip().rstrip(":") for ln in q["starter"].splitlines() if ln.startswith("def ")), q["func"])

    compile_err = next((e for e in events if e["type"] == "compile_error"), None)
    if compile_err:
        if compile_err["error_type"] in ("SyntaxError", "IndentationError", "TabError"):
            pointers.append(f"{compile_err['error_type']} on line {compile_err.get('line')}: {compile_err['message']}. "
                            "Check colons after def/if/for, matching parentheses/quotes, and consistent indentation.")
        else:
            pointers.append(f"Your code raised {compile_err['error_type']} while loading (before any test ran): "
                            f"{compile_err['message']}. Top-level code runs at import time.")
        return {"status": "error", "passed": 0, "total": len(tests), "tests": [],
                "compile_error": compile_err, "pointers": pointers}

    if any(e["type"] == "missing_function" for e in events):
        pointers.append(f"No function named `{q['func']}` was found. The grader calls `{signature}`. "
                        "Keep the exact name from the starter code.")
        return {"status": "error", "passed": 0, "total": len(tests), "tests": [], "pointers": pointers}

    if not events and stderr:
        return {"status": "error", "passed": 0, "total": len(tests), "tests": [],
                "pointers": ["The runner crashed unexpectedly."], "compile_error": {"error_type": "RunnerError", "message": stderr[-1500:]}}

    loaded = next((e for e in events if e["type"] == "loaded"), {})
    by_index = {e["index"]: e for e in events if e["type"] == "test"}
    results = []
    hit_timeout = False
    for i, t in enumerate(tests):
        r = by_index.get(i)
        if r is None:
            if timed_out and not hit_timeout:
                hit_timeout = True
                r = {"index": i, "passed": False, "timeout": True,
                     "input": t.get("label") or "(large input)"}
                pointers.append(f"Test {i + 1} exceeded the {TIME_LIMIT[mode]}s time limit. Either an infinite loop "
                                f"or an approach that's too slow for large input. {q.get('perf_hint', '')}".strip())
            else:
                r = {"index": i, "passed": False, "skipped": True, "input": t.get("label", "")}
        r["hidden"] = bool(t.get("hidden"))
        if not r.get("passed") and not r.get("skipped"):
            if t.get("why"):
                r["why"] = t["why"]
                pointers.append(f"Test {i + 1}: {t['why']}")
            pointers.extend(error_pointers(r, signature))
        results.append(r)

    passed = sum(1 for r in results if r.get("passed"))
    status = "passed" if passed == len(tests) else "failed"
    if status == "passed" and mode == "sample":
        pointers.append("Sample tests pass. Click **Submit** to run the hidden edge-case tests.")
    return {"status": status, "passed": passed, "total": len(tests), "tests": results,
            "pointers": dedupe(pointers), "module_stdout": loaded.get("stdout", "")}


def error_pointers(r, signature):
    out = []
    et, msg = r.get("error_type"), r.get("error", "")
    if et == "TypeError" and ("positional argument" in msg or "required" in msg):
        out.append(f"Function signature mismatch ({msg}). The grader calls `{signature}`.")
    elif et == "TypeError" and "NoneType" in msg:
        out.append("A value is None where you didn't expect it. A helper may be missing `return`, or an input field can be None.")
    elif et == "RecursionError":
        out.append("Recursion went too deep. Python's default limit is ~1000 frames. Use an iterative approach (loop + stack/queue).")
    elif et == "IndexError":
        out.append("IndexError: check loop bounds and empty-input edge cases.")
    elif et == "KeyError":
        out.append(f"KeyError {msg}: use `dict.get(key, default)` or check `key in d` first.")
    elif et == "ValueError" and "invalid literal" in msg:
        out.append("int() failed on a non-numeric string. Validate characters (e.g. `str.isdigit()`) before converting.")
    elif et == "ZeroDivisionError":
        out.append("Division by zero. Guard against empty input or zero-length windows.")
    elif et == "AttributeError" and "NoneType" in msg:
        out.append("You called a method on None. Handle missing/None values before using them.")
    elif et:
        out.append(f"{et}: {msg}")
    elif r.get("got_type") == "NoneType" and r.get("expected_type") != "NoneType":
        out.append("Your function returned None. Did you forget a `return` statement (or leave `pass` in)?")
    elif r.get("got_type") and r.get("expected_type") and r["got_type"] != r["expected_type"] \
            and {r["got_type"], r["expected_type"]} not in ({"int", "float"}, {"list", "tuple"}):
        out.append(f"Return type mismatch: expected `{r['expected_type']}` but got `{r['got_type']}`.")
    return out


def dedupe(items):
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# -------------------------------------------------------------------- sql ---

def execute_sql(sql):
    conn = Q.build_db()
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows
    finally:
        conn.close()


def sql_error_pointer(msg):
    m = msg.lower()
    if "no such column" in m:
        return "Unknown column. Check spelling and table aliases (open the Schema panel). If you aliased a table, use `alias.column`."
    if "no such table" in m:
        return "Unknown table. Available tables: sites, devices, interfaces, incidents, traffic."
    if "ambiguous column" in m:
        return "Ambiguous column: it exists in more than one joined table. Prefix it, e.g. `d.device_id`."
    if "misuse of aggregate" in m or "misuse of window" in m:
        return "Aggregates (COUNT/SUM/AVG) and window functions can't be used in WHERE. Use HAVING for aggregates, or wrap window functions in a CTE/subquery."
    if "one statement at a time" in m:
        return "Submit a single SQL statement (remove extra semicolons / queries)."
    if "syntax error" in m or "incomplete input" in m:
        return "Syntax error. Clause order is SELECT, FROM, JOIN ... ON, WHERE, GROUP BY, HAVING, ORDER BY. Check commas between columns and no trailing comma before FROM."
    if "readonly" in m or "attempt to write" in m:
        return "Only SELECT queries are graded."
    return None


def _norm_cell(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    return v


def _sort_key(row):
    return tuple((0, "") if v is None else (1, v) if isinstance(v, float) else (2, str(v)) for v in row)


def sql_submit(q, sql):
    try:
        cols, rows = execute_sql(sql)
    except sqlite3.Error as e:
        ptr = sql_error_pointer(str(e))
        return {"status": "error", "error": str(e), "pointers": [ptr] if ptr else []}

    exp_cols, exp_rows = execute_sql(q["solution"])
    pointers, notes = [], []
    status = "failed"

    if not cols:
        pointers.append("Your statement returned no result set. Write a SELECT query.")
    elif len(cols) != len(exp_cols):
        pointers.append(f"Expected {len(exp_cols)} column(s) ({', '.join(exp_cols)}) but you returned "
                        f"{len(cols)} ({', '.join(cols)}). Select exactly the requested columns, in order.")
    elif len(rows) != len(exp_rows):
        pointers.append(f"Expected {len(exp_rows)} row(s) but got {len(rows)}.")
        if len(rows) > len(exp_rows):
            pointers.append("Too many rows: a missing WHERE/HAVING filter, or a JOIN duplicating rows "
                            "(consider DISTINCT / EXISTS, or check you GROUP BY the right column).")
        else:
            pointers.append("Too few rows: an INNER JOIN may be dropping rows (LEFT JOIN?), a filter may be too strict, "
                            "or a NULL comparison like `= NULL` (use IS NULL).")
    else:
        u = [tuple(_norm_cell(v) for v in r) for r in rows]
        e = [tuple(_norm_cell(v) for v in r) for r in exp_rows]
        if u == e:
            status = "passed"
        elif sorted(u, key=_sort_key) == sorted(e, key=_sort_key):
            if q.get("ordered"):
                pointers.append("Your rows are correct but in the wrong order. Re-read the ORDER BY requirement "
                                "(including tie-breakers and ASC/DESC).")
            else:
                status = "passed"
        else:
            for idx, (ur, er) in enumerate(zip(u, e)):
                if ur != er:
                    diffs = [f"`{exp_cols[c]}`: expected {exp_rows[idx][c]!r}, got {rows[idx][c]!r}"
                             for c in range(len(er)) if ur[c] != er[c]]
                    pointers.append(f"First mismatch at row {idx + 1}: " + "; ".join(diffs[:3]))
                    if any(isinstance(er[c], float) and isinstance(ur[c], float) and er[c] != 0 and ur[c] == round(ur[c])
                           and er[c] != round(er[c]) for c in range(len(er))):
                        pointers.append("Looks like integer division truncated a value. Multiply by 100.0 (or CAST AS REAL) before dividing.")
                    break

    if status != "passed" and q.get("pitfalls"):
        pointers.append("Common pitfalls for this question: " + " | ".join(q["pitfalls"]))

    if cols and [c.lower() for c in cols] != [c.lower() for c in exp_cols] and len(cols) == len(exp_cols):
        notes.append(f"Column names differ (expected {', '.join(exp_cols)}). Values are what's graded, but use "
                     "`AS alias` to match. Some graders do check headers.")

    return {"status": status, "columns": cols, "rows": [list(r) for r in rows[:MAX_SQL_ROWS]],
            "row_count": len(rows), "expected_columns": exp_cols, "expected_rows": [list(r) for r in exp_rows],
            "pointers": pointers, "notes": notes}


def sql_run(sql):
    try:
        cols, rows = execute_sql(sql)
    except sqlite3.Error as e:
        ptr = sql_error_pointer(str(e))
        return {"status": "error", "error": str(e), "pointers": [ptr] if ptr else []}
    return {"status": "ok", "columns": cols, "rows": [list(r) for r in rows[:MAX_SQL_ROWS]], "row_count": len(rows)}


def schema_info():
    conn = Q.build_db()
    tables = []
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid"):
        cols = [{"name": c[1], "type": c[2]} for c in conn.execute(f"PRAGMA table_info({name})")]
        cur = conn.execute(f"SELECT * FROM {name}")
        rows = [list(r) for r in cur.fetchall()]
        tables.append({"name": name, "columns": cols, "rows": rows})
    conn.close()
    return {"ddl": Q.SQL_SCHEMA, "tables": tables}


# -------------------------------------------------------------------- api ---

PUBLIC_FIELDS = ("id", "type", "title", "difficulty", "category", "description", "starter", "hints", "options", "func")


def question_list():
    out = []
    for q in Q.ALL_QUESTIONS:
        item = {k: q[k] for k in PUBLIC_FIELDS if k in q}
        if q["type"] == "python":
            item["sample_count"] = sum(1 for t in q["tests"] if not t.get("hidden"))
            item["test_count"] = len(q["tests"])
        out.append(item)
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/questions":
            return self._send(200, question_list())
        if path == "/api/schema":
            return self._send(200, schema_info())
        if path == "/":
            path = "/index.html"
        target = (STATIC / path.lstrip("/")).resolve()
        if STATIC.resolve() not in target.parents or not target.is_file():
            return self._send(404, {"error": "not found"})
        self._send(200, target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "bad json"})

        if path == "/api/sql/run":
            return self._send(200, sql_run(body.get("code", "")))

        q = Q.BY_ID.get(body.get("id"))
        if not q:
            return self._send(404, {"error": "unknown question"})

        if path == "/api/run" and q["type"] == "python":
            mode = "submit" if body.get("mode") == "submit" else "sample"
            return self._send(200, run_python(q, body.get("code", ""), mode))
        if path == "/api/sql/submit" and q["type"] == "sql":
            return self._send(200, sql_submit(q, body.get("code", "")))
        if path == "/api/mcq" and q["type"] == "mcq":
            choice = body.get("choice")
            return self._send(200, {"correct": choice == q["answer"], "answer": q["answer"],
                                    "explanation": q["explanation"]})
        if path == "/api/solution":
            return self._send(200, {"solution": q.get("solution", "")})
        self._send(404, {"error": "unknown endpoint"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"TDP practice running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
