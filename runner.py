"""Sandboxed test runner. Reads a JSON payload on stdin and streams one JSON
result per line on stdout so the server can recover partial results if the
user's code hangs and the process is killed."""

import contextlib
import copy
import io
import json
import math
import sys
import time
import traceback

USER_FILE = "<your code>"
MAX_REPR = 400


def emit(obj):
    sys.__stdout__.write(json.dumps(obj) + "\n")
    sys.__stdout__.flush()


def short(value):
    text = repr(value)
    if len(text) > MAX_REPR:
        text = text[:MAX_REPR] + f"... ({len(text):,} chars)"
    return text


def norm(v):
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return v


def equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return a == b


def user_traceback(exc, code_lines):
    frames = []
    for fr in traceback.extract_tb(exc.__traceback__):
        if fr.filename == USER_FILE:
            src = code_lines[fr.lineno - 1].strip() if 0 < fr.lineno <= len(code_lines) else ""
            frames.append(f"line {fr.lineno}, in {fr.name}: {src}")
    return frames


def load(code, label):
    ns = {"__name__": "__solution__"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, label, "exec"), ns)
    return ns, buf.getvalue()


def main():
    payload = json.loads(sys.stdin.read())
    func = payload["func"]
    code = payload["code"]
    code_lines = code.splitlines()

    ref_ns, _ = load(payload["reference"], "<reference>")
    reference = ref_ns[func]

    try:
        user_ns, module_out = load(code, USER_FILE)
    except SyntaxError as e:
        emit({"type": "compile_error", "error_type": type(e).__name__,
              "message": e.msg, "line": e.lineno, "text": (e.text or "").rstrip()})
        return
    except BaseException as e:
        emit({"type": "compile_error", "error_type": type(e).__name__, "message": str(e),
              "traceback": user_traceback(e, code_lines)})
        return

    if not callable(user_ns.get(func)):
        emit({"type": "missing_function", "func": func})
        return
    emit({"type": "loaded", "stdout": module_out})
    user_fn = user_ns[func]

    for i, test in enumerate(payload["tests"]):
        args = test["args"] if "args" in test else eval(test["args_code"])
        expected = norm(reference(*copy.deepcopy(args)))
        label = test.get("label") or f"{func}({', '.join(short(a) for a in args)})"

        buf = io.StringIO()
        result = {"type": "test", "index": i, "input": label,
                  "expected": short(expected), "expected_type": type(expected).__name__}
        start = time.perf_counter()
        try:
            with contextlib.redirect_stdout(buf):
                got = user_fn(*copy.deepcopy(args))
            elapsed = time.perf_counter() - start
            result.update(passed=equal(norm(got), expected), got=short(got), got_type=type(got).__name__)
        except BaseException as e:
            elapsed = time.perf_counter() - start
            result.update(passed=False, error_type=type(e).__name__, error=str(e),
                          traceback=user_traceback(e, code_lines))
        result["time_ms"] = round(elapsed * 1000, 2)
        result["stdout"] = buf.getvalue()[:2000]
        emit(result)

    emit({"type": "done"})


if __name__ == "__main__":
    main()
