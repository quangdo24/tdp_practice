# TDP Practice: Network Engineering

A HackerRank-style practice app for the **AT&T Technology Development Program (TDP)** technical assessment, Network Engineering track. Write code in the browser, check it against tests (including hidden edge cases), and get specific feedback on what went wrong.

There are 46 questions in three categories:

| Category | Count | What it covers |
| --- | --- | --- |
| Python | 14 | IPv4 validation, subnetting, MAC normalization, BFS hop counts, longest-prefix routing, log parsing, data cleaning, sliding windows |
| SQL | 14 | Filtering, GROUP BY / HAVING, LEFT JOIN anti-joins, NULL handling, date math, CTEs, window functions (`ROW_NUMBER`, `LAG`) |
| Concepts | 18 | Multiple choice on OSI, subnetting, TCP/UDP, ARP, DNS, BGP/OSPF, VLANs, NAT, DHCP, and SQL/Python fundamentals |

## Getting started

You need Python 3.8 or newer. There's nothing to install.

```bash
git clone https://github.com/quangdo24/tdp_practice.git
cd tdp_practice
python3 server.py
```

Your browser opens at <http://127.0.0.1:8000>. Options:

```bash
python3 server.py --port 9000      # use a different port
python3 server.py --no-browser     # don't open a browser automatically
```

The code editor (CodeMirror) loads from a CDN. If you're offline, a plain text editor is used instead.

## How to use it

- **Python questions:** **Run samples** runs only the visible examples. **Submit** runs every test, including the hidden edge cases. You'll see each test's input, expected output, your output, anything your code printed, and the line where an error occurred.
- **SQL questions:** queries run against an in-memory SQLite network inventory database. **Run query** shows your output without grading it. **Submit** compares your output to the expected result. Open **Database schema & data** to browse every table.
- **Concepts:** choose an answer and click **Check answer** to see an explanation.
- **Hints** are revealed one at a time. The **reference solution** is behind a confirmation prompt, so try the hints first.
- Your code, hints, and progress are saved in your browser's localStorage. **Reset progress** clears them.

Keyboard shortcuts:

| Shortcut | Action |
| --- | --- |
| `⌘/Ctrl + Enter` | Run |
| `⌘/Ctrl + Shift + Enter` | Submit |

## Feedback

When an answer is wrong, the app tries to explain why:

- **Edge-case tests** explain what they check, for example "`int(' 1') == 1`, so validate characters explicitly."
- **Python errors** are matched to likely causes: a missing `return`, the wrong function name or signature, a `RecursionError` on deep inputs, a `KeyError` on missing fields, and so on.
- **Performance:** some problems include large inputs. Code that's too slow hits the time limit and gets a hint toward a faster approach, such as a sliding window or BFS.
- **SQL** results are compared on column count, row count, row order, and cell values. Common traps are flagged: `= NULL` instead of `IS NULL`, integer division, `COUNT(*)` after a LEFT JOIN, and duplicate rows from joins.

## Database schema

```
sites       (site_code, city, state, region)
devices     (device_id, hostname, site_code, vendor, device_type, install_date)
interfaces  (interface_id, device_id, name, speed_mbps, status)        -- up | down | admin-down
incidents   (incident_id, device_id, opened_at, closed_at, severity, category)  -- closed_at NULL = open
traffic     (device_id, sample_date, gb_in, gb_out)
```

## Project structure

```
server.py         Local HTTP server (standard library only): API, grading, and feedback
runner.py         Runs your Python code in a subprocess with a time limit and streams per-test results
questions.py      Question bank, SQL schema, and seed data
static/
  index.html      Page layout
  app.js          Editor, question list, and result rendering
  style.css       Styles
```

## Adding questions

All questions live in `questions.py`.

**Python:** add an entry to `PYTHON_QUESTIONS` with `func`, `description`, `starter`, `solution`, `hints`, and `tests`. You don't write expected outputs, because they're computed by running `solution`. Each test only needs inputs:

```python
{"args": ["192.168.01.1"], "hidden": True, "why": "Leading zeros are not allowed."}
```

For large inputs, use `args_code` (a Python expression the runner evaluates) together with a short `label` for display.

**SQL:** add an entry to `SQL_QUESTIONS` with a reference `solution` query, `ordered: True` if row order matters, `hints`, and optional `pitfalls`.

**Concepts:** add an entry to `MCQ_QUESTIONS` with `options`, the `answer` index, and an `explanation`.

## Notes

- Python code runs locally in a separate process with a time limit (5s for samples, 10s for submit). The server only listens on `127.0.0.1`. It's a practice tool and doesn't sandbox untrusted code.
- SQL uses the SQLite dialect. Date functions differ from MySQL and PostgreSQL. For example, use `julianday()` here where MySQL uses `TIMESTAMPDIFF`.
- The questions are practice material modeled on typical entry-level assessments. They aren't actual AT&T assessment questions.
