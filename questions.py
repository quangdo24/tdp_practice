"""Question bank for the AT&T TDP (Network Engineering) practice app.

Three question types:
  - python: implement a function; graded against tests. Expected values are
    computed by running `solution`, so tests only need inputs (+ an optional
    `why` explaining what edge case the test covers).
  - sql:    write a query against the network inventory DB (see SQL_SEED).
            Graded by comparing your result set to the reference query's.
  - mcq:    networking / CS fundamentals multiple choice.
"""

import sqlite3
from textwrap import dedent


def D(s):
    return dedent(s).strip("\n")


# --------------------------------------------------------------------------
# PYTHON
# --------------------------------------------------------------------------

PYTHON_QUESTIONS = [
    {
        "id": "py-valid-ipv4",
        "title": "Validate an IPv4 Address",
        "difficulty": "Easy",
        "category": "Python · Networking",
        "func": "valid_ipv4",
        "description": D("""
            Write `valid_ipv4(s)` that returns `True` if the string `s` is a valid
            dotted-decimal IPv4 address and `False` otherwise.

            A valid address:
            - has exactly **4** octets separated by `.`
            - each octet contains only digits `0-9` (no spaces, signs, or letters)
            - each octet is between **0 and 255**
            - has **no leading zeros** (`"01"` is invalid, `"0"` is fine)

            ```
            valid_ipv4("192.168.1.1")   -> True
            valid_ipv4("10.0.0.256")    -> False   # 256 > 255
            valid_ipv4("192.168.01.1")  -> False   # leading zero
            ```
        """),
        "starter": D("""
            def valid_ipv4(s):
                # your code here
                pass
        """),
        "solution": D("""
            def valid_ipv4(s):
                parts = s.split(".")
                if len(parts) != 4:
                    return False
                for p in parts:
                    if not p or not (p.isascii() and p.isdigit()):
                        return False
                    if len(p) > 1 and p[0] == "0":
                        return False
                    if int(p) > 255:
                        return False
                return True
        """),
        "hints": [
            "Start with `s.split('.')` and check you get exactly 4 parts.",
            "`int(' 1')` and `int('+1')` both return 1 — so validate characters with `str.isdigit()` before converting.",
            "Leading zero check: `len(p) > 1 and p[0] == '0'`.",
        ],
        "tests": [
            {"args": ["192.168.1.1"]},
            {"args": ["10.0.0.256"], "why": "Each octet must be between 0 and 255."},
            {"args": ["0.0.0.0"], "hidden": True, "why": "All-zero octets are valid."},
            {"args": ["255.255.255.255"], "hidden": True, "why": "255 is the max valid octet."},
            {"args": ["192.168.1"], "hidden": True, "why": "Need exactly 4 octets."},
            {"args": ["1.2.3.4.5"], "hidden": True, "why": "Need exactly 4 octets."},
            {"args": ["192.168.01.1"], "hidden": True, "why": "Leading zeros like '01' are not allowed."},
            {"args": ["192.168.1.1."], "hidden": True, "why": "A trailing dot creates an empty 5th octet."},
            {"args": ["1..1.1"], "hidden": True, "why": "Empty octets are invalid (and int('') raises ValueError)."},
            {"args": ["a.b.c.d"], "hidden": True, "why": "Octets must be numeric."},
            {"args": [""], "hidden": True, "why": "Empty string is invalid."},
            {"args": [" 1.1.1.1"], "hidden": True, "why": "int(' 1') == 1, so int() alone accepts whitespace. Validate characters explicitly."},
            {"args": ["+1.1.1.1"], "hidden": True, "why": "int('+1') == 1 too. Check every character is a digit."},
            {"args": ["999.1.1.1"], "hidden": True, "why": "999 is out of range."},
        ],
    },
    {
        "id": "py-usable-hosts",
        "title": "Usable Hosts in a Subnet",
        "difficulty": "Easy",
        "category": "Python · Networking",
        "func": "usable_hosts",
        "description": D("""
            Write `usable_hosts(prefix)` that returns the number of usable host
            addresses for an IPv4 CIDR prefix length (e.g. `24` for a `/24`).

            Rules:
            - Normally usable hosts = 2^(32 - prefix) - 2 (network + broadcast are reserved)
            - `/31` -> **2** (point-to-point links, RFC 3021)
            - `/32` -> **1** (single host route)
            - prefix outside 0..32 -> **-1**

            ```
            usable_hosts(24) -> 254
            usable_hosts(30) -> 2
            usable_hosts(33) -> -1
            ```
        """),
        "starter": D("""
            def usable_hosts(prefix):
                # your code here
                pass
        """),
        "solution": D("""
            def usable_hosts(prefix):
                if prefix < 0 or prefix > 32:
                    return -1
                if prefix == 32:
                    return 1
                if prefix == 31:
                    return 2
                return 2 ** (32 - prefix) - 2
        """),
        "hints": [
            "Handle the special cases (invalid, /31, /32) first, then the general formula.",
            "In Python `2 ** n` (or `1 << n`) gives 2 to the power n. Don't use `^` — that's XOR!",
        ],
        "tests": [
            {"args": [24]},
            {"args": [30]},
            {"args": [26], "hidden": True, "why": "/26 -> 64 addresses - 2 = 62."},
            {"args": [8], "hidden": True, "why": "/8 -> 2^24 - 2."},
            {"args": [0], "hidden": True, "why": "/0 -> 2^32 - 2."},
            {"args": [31], "hidden": True, "why": "/31 is a special case: 2 usable (RFC 3021)."},
            {"args": [32], "hidden": True, "why": "/32 is a single host: 1."},
            {"args": [33], "hidden": True, "why": "Prefix > 32 is invalid -> -1."},
            {"args": [-1], "hidden": True, "why": "Negative prefix is invalid -> -1."},
        ],
    },
    {
        "id": "py-status-runs",
        "title": "Compress Interface Status History",
        "difficulty": "Easy",
        "category": "Python · Data",
        "func": "status_runs",
        "description": D("""
            A monitoring system polls an interface every minute and records its
            status. Write `status_runs(statuses)` that compresses consecutive
            identical statuses into `[status, count]` pairs (run-length encoding).

            ```
            status_runs(["up", "up", "down", "down", "down", "up"])
            -> [["up", 2], ["down", 3], ["up", 1]]

            status_runs([]) -> []
            ```
        """),
        "starter": D("""
            def status_runs(statuses):
                # your code here
                pass
        """),
        "solution": D("""
            def status_runs(statuses):
                runs = []
                for s in statuses:
                    if runs and runs[-1][0] == s:
                        runs[-1][1] += 1
                    else:
                        runs.append([s, 1])
                return runs
        """),
        "hints": [
            "Walk the list once, keeping track of the current status and its count.",
            "Compare each item against the last run you appended (`runs[-1]`).",
        ],
        "tests": [
            {"args": [["up", "up", "down", "down", "down", "up"]]},
            {"args": [[]], "why": "Empty input -> empty list."},
            {"args": [["down"]], "hidden": True, "why": "Single element. Make sure the final run gets added."},
            {"args": [["up", "up", "up"]], "hidden": True, "why": "One long run. Don't forget to flush the last run."},
            {"args": [["up", "down", "up", "down"]], "hidden": True, "why": "Alternating values -> every run has count 1."},
            {"args": [["admin-down", "admin-down", "up"]], "hidden": True},
        ],
    },
    {
        "id": "py-vendor-summary",
        "title": "Clean & Summarize Vendor Inventory",
        "difficulty": "Easy",
        "category": "Python · Data",
        "func": "vendor_summary",
        "description": D("""
            You receive device inventory as a list of dicts, exported from a messy
            spreadsheet. Write `vendor_summary(devices)` that counts devices per
            vendor and returns a list of `[vendor, count]` pairs.

            Data cleaning rules:
            - Vendor names are case-insensitive and may have surrounding spaces:
              normalize with strip + lowercase (`" CISCO "` -> `"cisco"`)
            - If the `"vendor"` key is missing, empty, or `None`, count it as `"unknown"`

            Sort by **count descending**, then **vendor name ascending**.

            ```
            vendor_summary([
                {"hostname": "r1", "vendor": "Cisco"},
                {"hostname": "r2", "vendor": "Juniper"},
                {"hostname": "r3", "vendor": " cisco "},
            ])
            -> [["cisco", 2], ["juniper", 1]]
            ```
        """),
        "starter": D("""
            def vendor_summary(devices):
                # your code here
                pass
        """),
        "solution": D("""
            def vendor_summary(devices):
                counts = {}
                for d in devices:
                    vendor = (d.get("vendor") or "").strip().lower() or "unknown"
                    counts[vendor] = counts.get(vendor, 0) + 1
                ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
                return [[v, c] for v, c in ranked]
        """),
        "hints": [
            "`d.get('vendor')` returns None instead of raising KeyError when the key is missing.",
            "`(value or '')` turns None into an empty string so `.strip()` is safe.",
            "Sort with a tuple key: `key=lambda kv: (-kv[1], kv[0])`.",
        ],
        "tests": [
            {"args": [[{"hostname": "r1", "vendor": "Cisco"}, {"hostname": "r2", "vendor": "Juniper"}, {"hostname": "r3", "vendor": " cisco "}]]},
            {"args": [[{"hostname": "a", "vendor": " CISCO "}, {"hostname": "b", "vendor": "cisco"}, {"hostname": "c", "vendor": "Arista"}, {"hostname": "d", "vendor": "arista "}]],
             "hidden": True, "why": "Normalize with strip().lower(). Equal counts sort alphabetically."},
            {"args": [[{"hostname": "x"}, {"hostname": "y", "vendor": ""}, {"hostname": "z", "vendor": "Nokia"}]],
             "hidden": True, "why": "Missing or empty vendor counts as 'unknown'. Use dict.get()."},
            {"args": [[{"hostname": "x", "vendor": None}]], "hidden": True,
             "why": "vendor can be None, and None.strip() raises AttributeError."},
            {"args": [[{"hostname": "x", "vendor": "   "}]], "hidden": True,
             "why": "A whitespace-only vendor is empty after strip(), so it's 'unknown'."},
            {"args": [[]], "hidden": True, "why": "Empty inventory -> []."},
        ],
    },
    {
        "id": "py-count-errors",
        "title": "Parse Syslog: Errors per Device",
        "difficulty": "Easy",
        "category": "Python · Data",
        "func": "count_errors",
        "description": D("""
            Each log line has the format:

            ```
            <date> <time> <hostname> <LEVEL> <message...>
            ```

            Write `count_errors(logs)` that returns a dict mapping each hostname to
            the number of lines whose LEVEL is `ERROR` or `CRITICAL`.

            - LEVEL can appear in any case (`error`, `Critical`, ...)
            - Fields may be separated by **one or more** spaces
            - Lines with fewer than 5 fields are malformed: skip them
            - Hosts with zero errors must **not** appear in the result

            ```
            count_errors([
              "2026-10-01 08:00:01 dal1-core-01 ERROR BGP neighbor down",
              "2026-10-01 08:00:05 dal1-core-01 INFO interface up",
              "2026-10-01 08:01:10 nyc1-fw-01 CRITICAL fan failure",
            ])
            -> {"dal1-core-01": 1, "nyc1-fw-01": 1}
            ```
        """),
        "starter": D("""
            def count_errors(logs):
                # your code here
                pass
        """),
        "solution": D("""
            def count_errors(logs):
                counts = {}
                for line in logs:
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    host, level = parts[2], parts[3].upper()
                    if level in ("ERROR", "CRITICAL"):
                        counts[host] = counts.get(host, 0) + 1
                return counts
        """),
        "hints": [
            "`line.split()` with no argument splits on any run of whitespace.",
            "Hostname is field index 2 and level is index 3. Don't search the whole line for 'ERROR'.",
            "`collections.Counter` or `dict.get(k, 0) + 1` are handy for counting.",
        ],
        "tests": [
            {"args": [[
                "2026-10-01 08:00:01 dal1-core-01 ERROR BGP neighbor 10.0.0.2 down",
                "2026-10-01 08:00:05 dal1-core-01 INFO interface ge-0/0/1 up",
                "2026-10-01 08:01:10 nyc1-fw-01 CRITICAL fan failure",
                "2026-10-01 08:02:00 dal1-core-01 ERROR BGP neighbor 10.0.0.2 flap",
            ]]},
            {"args": [[
                "2026-10-01 09:00:00 sea1-acc-01 error crc errors on Gi1/0/1",
                "2026-10-01 09:00:01 sea1-acc-01 Critical power supply 2 failed",
                "2026-10-01 09:00:02 sea1-acc-01 warning high cpu",
            ]], "hidden": True, "why": "LEVEL can be any case. Normalize with .upper()."},
            {"args": [[
                "garbage",
                "2026-10-01 09:00:00 chi1-core-01 ERROR",
                "2026-10-01 09:00:00 chi1-core-01 ERROR link down",
            ]], "hidden": True, "why": "Lines with fewer than 5 fields are malformed. Skip them, don't crash."},
            {"args": [["2026-10-01  09:00:00   atl1-core-01   ERROR    ospf adjacency lost"]],
             "hidden": True, "why": "Multiple spaces between fields. Use split() with no argument."},
            {"args": [["2026-10-01 09:00:00 lax1-core-01 INFO cleared ERROR state"]],
             "hidden": True, "why": "The word ERROR in the message doesn't count. Only the 4th field is the level."},
            {"args": [["2026-10-01 09:00:00 x INFO ok"]], "hidden": True,
             "why": "Hosts with zero errors should not appear in the dict."},
            {"args": [[]], "hidden": True, "why": "Empty input -> {}."},
        ],
    },
    {
        "id": "py-network-address",
        "title": "Compute the Network Address",
        "difficulty": "Medium",
        "category": "Python · Networking",
        "func": "network_address",
        "description": D("""
            Write `network_address(ip, prefix)` that returns the network address
            (as a dotted string) for IPv4 address `ip` with CIDR prefix length
            `prefix` (0-32). Inputs are always valid.

            ```
            network_address("192.168.1.130", 25) -> "192.168.1.128"
            network_address("10.20.30.40", 8)    -> "10.0.0.0"
            ```

            Try it **without** the `ipaddress` module. Interviewers want to see
            the bit math.
        """),
        "starter": D("""
            def network_address(ip, prefix):
                # your code here
                pass
        """),
        "solution": D("""
            def network_address(ip, prefix):
                n = 0
                for octet in ip.split("."):
                    n = (n << 8) | int(octet)
                mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
                n &= mask
                return ".".join(str((n >> shift) & 255) for shift in (24, 16, 8, 0))
        """),
        "hints": [
            "Convert the IP to a single 32-bit integer: `n = (n << 8) | int(octet)` for each octet.",
            "The mask is `prefix` one-bits followed by zeros: `(0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF`.",
            "AND the IP with the mask, then convert back: `(n >> 24) & 255`, `(n >> 16) & 255`, ...",
        ],
        "tests": [
            {"args": ["192.168.1.130", 25]},
            {"args": ["10.20.30.40", 8]},
            {"args": ["172.16.5.4", 12], "hidden": True, "why": "/12 boundary falls inside the 2nd octet (255.240.0.0)."},
            {"args": ["172.31.200.9", 12], "hidden": True, "why": "172.31.x.x is still inside 172.16.0.0/12."},
            {"args": ["10.1.255.255", 23], "hidden": True, "why": "/23 = 255.255.254.0 clears the low bit of the 3rd octet."},
            {"args": ["192.168.1.1", 32], "hidden": True, "why": "/32 -> the address itself."},
            {"args": ["192.168.1.1", 0], "hidden": True, "why": "/0 -> 0.0.0.0."},
            {"args": ["8.8.8.8", 30], "hidden": True},
        ],
    },
    {
        "id": "py-same-subnet",
        "title": "Are Two Hosts on the Same Subnet?",
        "difficulty": "Medium",
        "category": "Python · Networking",
        "func": "same_subnet",
        "description": D("""
            Write `same_subnet(ip1, ip2, mask)` that returns `True` if both IPv4
            addresses are in the same network given a dotted-decimal subnet mask
            (e.g. `"255.255.255.0"`). Inputs are always valid.

            ```
            same_subnet("192.168.1.10", "192.168.1.200", "255.255.255.0") -> True
            same_subnet("10.0.0.1", "10.0.0.130", "255.255.255.128")      -> False
            ```
        """),
        "starter": D("""
            def same_subnet(ip1, ip2, mask):
                # your code here
                pass
        """),
        "solution": D("""
            def same_subnet(ip1, ip2, mask):
                def to_int(addr):
                    n = 0
                    for octet in addr.split("."):
                        n = (n << 8) | int(octet)
                    return n
                m = to_int(mask)
                return (to_int(ip1) & m) == (to_int(ip2) & m)
        """),
        "hints": [
            "Two hosts share a subnet when `(ip1 AND mask) == (ip2 AND mask)`.",
            "You can AND octet-by-octet, or convert everything to 32-bit integers first.",
        ],
        "tests": [
            {"args": ["192.168.1.10", "192.168.1.200", "255.255.255.0"]},
            {"args": ["192.168.1.10", "192.168.2.10", "255.255.255.0"]},
            {"args": ["10.0.0.1", "10.0.0.130", "255.255.255.128"], "hidden": True, "why": "A /25 splits the last octet at 128."},
            {"args": ["10.0.0.1", "10.0.0.126", "255.255.255.128"], "hidden": True, "why": "Both are below 128 in a /25."},
            {"args": ["172.16.0.1", "172.31.255.254", "255.240.0.0"], "hidden": True, "why": "A /12 mask spans 172.16-172.31."},
            {"args": ["1.1.1.1", "2.2.2.2", "0.0.0.0"], "hidden": True, "why": "Mask 0.0.0.0 puts every address in one network."},
            {"args": ["10.0.0.1", "10.0.0.2", "255.255.255.255"], "hidden": True, "why": "A /32 mask means each host is its own network."},
        ],
    },
    {
        "id": "py-top-talkers",
        "title": "Top Talkers from Flow Records",
        "difficulty": "Medium",
        "category": "Python · Data",
        "func": "top_talkers",
        "description": D("""
            NetFlow-style records are given as `[src_ip, dst_ip, bytes]`. Write
            `top_talkers(flows, k)` that returns the `k` source IPs that sent the
            most **total** bytes.

            - Sort by total bytes **descending**
            - Break ties by source IP **string** ascending (plain string comparison)
            - If there are fewer than `k` sources, return them all

            ```
            flows = [
              ["10.0.0.1", "10.0.0.9", 500],
              ["10.0.0.2", "10.0.0.9", 300],
              ["10.0.0.1", "10.0.0.8", 200],
              ["10.0.0.3", "10.0.0.9", 900],
            ]
            top_talkers(flows, 2) -> ["10.0.0.3", "10.0.0.1"]   # 900, 700
            ```
        """),
        "starter": D("""
            def top_talkers(flows, k):
                # your code here
                pass
        """),
        "solution": D("""
            def top_talkers(flows, k):
                totals = {}
                for src, dst, nbytes in flows:
                    totals[src] = totals.get(src, 0) + nbytes
                ranked = sorted(totals, key=lambda ip: (-totals[ip], ip))
                return ranked[:k]
        """),
        "hints": [
            "First aggregate: build a dict `src -> total bytes`.",
            "Then sort with a compound key `(-total, ip)` so higher totals come first and ties go alphabetical.",
            "Slicing past the end of a list is safe: `ranked[:k]`.",
        ],
        "tests": [
            {"args": [[["10.0.0.1", "10.0.0.9", 500], ["10.0.0.2", "10.0.0.9", 300], ["10.0.0.1", "10.0.0.8", 200], ["10.0.0.3", "10.0.0.9", 900]], 2]},
            {"args": [[["10.0.0.5", "x", 100], ["10.0.0.4", "x", 100], ["10.0.0.6", "x", 50]], 2], "hidden": True,
             "why": "Ties are broken by IP string ascending."},
            {"args": [[["10.0.0.10", "x", 5], ["10.0.0.9", "x", 5]], 2], "hidden": True,
             "why": "String comparison: '10.0.0.10' < '10.0.0.9' because '1' < '9'."},
            {"args": [[["a", "b", 1]], 5], "hidden": True, "why": "k larger than the number of sources -> return all."},
            {"args": [[["a", "b", 1]], 0], "hidden": True, "why": "k = 0 -> []."},
            {"args": [[], 3], "hidden": True, "why": "No flows -> []."},
            {"args": [[["s1", "d", 10], ["s2", "d", 30], ["s1", "d", 25]], 1], "hidden": True,
             "why": "Sum bytes per source before ranking (s1 = 35 > s2 = 30)."},
        ],
    },
    {
        "id": "py-merge-windows",
        "title": "Merge Maintenance Windows",
        "difficulty": "Medium",
        "category": "Python · Data",
        "func": "merge_windows",
        "description": D("""
            Change-management gives you maintenance windows as `[start, end]`
            minute offsets (inclusive). Write `merge_windows(windows)` that merges
            all overlapping **or touching** windows and returns them sorted by start.

            ```
            merge_windows([[1, 3], [2, 6], [8, 10], [15, 18]])
            -> [[1, 6], [8, 10], [15, 18]]

            merge_windows([[1, 4], [4, 5]]) -> [[1, 5]]   # touching
            ```
        """),
        "starter": D("""
            def merge_windows(windows):
                # your code here
                pass
        """),
        "solution": D("""
            def merge_windows(windows):
                merged = []
                for start, end in sorted(windows):
                    if merged and start <= merged[-1][1]:
                        merged[-1][1] = max(merged[-1][1], end)
                    else:
                        merged.append([start, end])
                return merged
        """),
        "hints": [
            "Sort by start time first. Then you only ever compare against the last merged window.",
            "Overlap/touch condition: `start <= last_end`.",
            "When merging, the new end is `max(last_end, end)`. A window can be fully nested inside another.",
        ],
        "tests": [
            {"args": [[[1, 3], [2, 6], [8, 10], [15, 18]]]},
            {"args": [[[1, 4], [4, 5]]], "why": "Touching windows (end == next start) merge."},
            {"args": [[[8, 10], [1, 3], [2, 6]]], "hidden": True, "why": "Input may be unsorted. Sort by start first."},
            {"args": [[[1, 10], [2, 3], [4, 5]]], "hidden": True, "why": "Nested windows: use max() so the end doesn't shrink."},
            {"args": [[]], "hidden": True, "why": "No windows -> []."},
            {"args": [[[5, 5]]], "hidden": True, "why": "Single zero-length window."},
            {"args": [[[1, 2], [3, 4]]], "hidden": True, "why": "2 and 3 don't overlap or touch, so don't merge."},
        ],
    },
    {
        "id": "py-normalize-mac",
        "title": "Normalize MAC Addresses",
        "difficulty": "Medium",
        "category": "Python · Networking",
        "func": "normalize_mac",
        "description": D("""
            Different vendors print MAC addresses differently. Write
            `normalize_mac(s)` that converts any of these **exact** formats to
            lowercase colon format `aa:bb:cc:dd:ee:ff`:

            - `AA:BB:CC:DD:EE:FF`  (colon, 6 groups of 2)
            - `AA-BB-CC-DD-EE-FF`  (hyphen, 6 groups of 2)
            - `aabb.ccdd.eeff`     (Cisco dot, 3 groups of 4)
            - `AABBCCDDEEFF`       (12 bare hex digits)

            Leading/trailing whitespace should be ignored. Anything else (mixed
            separators, wrong group sizes, non-hex chars) returns `None`.

            ```
            normalize_mac("00-1A-2B-3C-4D-5E") -> "00:1a:2b:3c:4d:5e"
            normalize_mac("aabb.ccdd.eeff")    -> "aa:bb:cc:dd:ee:ff"
            normalize_mac("AA:BB-CC:DD:EE:FF") -> None
            ```
        """),
        "starter": D("""
            def normalize_mac(s):
                # your code here
                pass
        """),
        "solution": D(r"""
            import re

            def normalize_mac(s):
                s = s.strip()
                h = "[0-9A-Fa-f]"
                patterns = [
                    rf"{h}{{2}}(:{h}{{2}}){{5}}",
                    rf"{h}{{2}}(-{h}{{2}}){{5}}",
                    rf"{h}{{4}}(\.{h}{{4}}){{2}}",
                    rf"{h}{{12}}",
                ]
                if not any(re.fullmatch(p, s) for p in patterns):
                    return None
                digits = re.sub(r"[^0-9A-Fa-f]", "", s).lower()
                return ":".join(digits[i:i + 2] for i in range(0, 12, 2))
        """),
        "hints": [
            "Validate the *shape* first (one regex per allowed format, using `re.fullmatch`), then extract the 12 hex digits.",
            "Mixed separators like `AA:BB-CC...` pass if you just strip all separators. That's why you validate the format first.",
            "Rebuild with `':'.join(digits[i:i+2] for i in range(0, 12, 2))`.",
        ],
        "tests": [
            {"args": ["AA:BB:CC:DD:EE:FF"]},
            {"args": ["aabb.ccdd.eeff"]},
            {"args": ["00-1A-2B-3C-4D-5E"], "hidden": True, "why": "Hyphen format."},
            {"args": ["001A2B3C4D5E"], "hidden": True, "why": "Bare 12 hex digits."},
            {"args": ["  aa:bb:cc:dd:ee:ff  "], "hidden": True, "why": "Strip leading/trailing whitespace."},
            {"args": ["AA:BB-CC:DD:EE:FF"], "hidden": True, "why": "Mixed separators are invalid -> None."},
            {"args": ["AA:BB:CC:DD:EE"], "hidden": True, "why": "Only 5 groups -> None."},
            {"args": ["GG:BB:CC:DD:EE:FF"], "hidden": True, "why": "'G' isn't a hex digit -> None."},
            {"args": ["aab.bccd.deeff"], "hidden": True, "why": "Dot format needs 3 groups of exactly 4 -> None."},
            {"args": ["aabb.ccdd.eef"], "hidden": True, "why": "Too few digits -> None."},
            {"args": [""], "hidden": True, "why": "Empty string -> None."},
        ],
    },
    {
        "id": "py-balanced-config",
        "title": "Validate Config Bracket Structure",
        "difficulty": "Medium",
        "category": "Python · Data",
        "func": "balanced_config",
        "description": D("""
            Router configs (Junos-style) use nested `{}`, `[]`, and `()`. Write
            `balanced_config(text)` that returns `True` if every bracket is closed
            by the matching type in the correct order.

            Twist: text inside **double quotes** is a literal string, so brackets
            inside quotes must be ignored. Quotes are never escaped.

            ```
            balanced_config('interface ge-0/0/1 { description "uplink"; mtu 9000; }') -> True
            balanced_config('policy { term a { from [ 10.0.0.0/8 ] }')                -> False
            balanced_config('description "has } brace";')                            -> True
            ```
        """),
        "starter": D("""
            def balanced_config(text):
                # your code here
                pass
        """),
        "solution": D("""
            def balanced_config(text):
                pairs = {")": "(", "]": "[", "}": "{"}
                stack = []
                in_quote = False
                for ch in text:
                    if ch == '"':
                        in_quote = not in_quote
                    elif in_quote:
                        continue
                    elif ch in "([{":
                        stack.append(ch)
                    elif ch in pairs:
                        if not stack or stack.pop() != pairs[ch]:
                            return False
                return not stack
        """),
        "hints": [
            "Classic stack problem: push openers, pop on closers and check the type matches.",
            "Keep a boolean `in_quote` that flips on every `\"`. While it's True, skip brackets.",
            "At the end, the stack must be empty. Also check for an empty stack *before* popping.",
        ],
        "tests": [
            {"args": ['interface ge-0/0/1 { description "uplink"; mtu 9000; }']},
            {"args": ["policy { term a { from [ 10.0.0.0/8 ] }"], "why": "An unclosed '{' -> False."},
            {"args": ['description "text with } brace";'], "hidden": True, "why": "Brackets inside double quotes are literal text."},
            {"args": ["set x ( a ]"], "hidden": True, "why": "Closer type must match the most recent opener."},
            {"args": [""], "hidden": True, "why": "Empty config is balanced."},
            {"args": ["}{"], "hidden": True, "why": "A closer with nothing open: check for an empty stack before popping."},
            {"args": ["a { b [ c ( d ) ] }"], "hidden": True, "why": "Properly nested."},
            {"args": ['{ "unclosed { in quotes" '], "hidden": True, "why": "Only the outer '{' counts and it's never closed."},
            {"args": ['"[" ]'], "hidden": True, "why": "']' outside quotes with nothing open -> False."},
        ],
    },
    {
        "id": "py-latency-alerts",
        "title": "Rolling Latency Alerts",
        "difficulty": "Medium",
        "category": "Python · Data",
        "func": "latency_alerts",
        "description": D("""
            Given a list of latency samples (ms), a window size `k`, and a
            `threshold`, return the **start index** of every window of `k`
            consecutive samples whose **average is strictly greater** than
            `threshold`.

            If `k` is larger than the list, return `[]`.

            ```
            latency_alerts([10, 20, 30, 40, 50], 2, 30) -> [2, 3]
            # window averages: 15, 25, 35, 45
            ```

            **Performance:** `len(latencies)` can be 1,000,000 with `k` = 50,000.
            An O(n·k) solution will time out. Aim for O(n).
        """),
        "starter": D("""
            def latency_alerts(latencies, k, threshold):
                # your code here
                pass
        """),
        "solution": D("""
            def latency_alerts(latencies, k, threshold):
                n = len(latencies)
                if k <= 0 or k > n:
                    return []
                window = sum(latencies[:k])
                limit = threshold * k
                result = []
                for i in range(n - k + 1):
                    if i > 0:
                        window += latencies[i + k - 1] - latencies[i - 1]
                    if window > limit:
                        result.append(i)
                return result
        """),
        "perf_hint": "Use a sliding window: keep a running sum, add the element entering the window and subtract the one leaving.",
        "hints": [
            "There are `n - k + 1` windows, starting at indices 0 .. n-k.",
            "Don't recompute `sum(latencies[i:i+k])` each time. That's O(k) per window.",
            "Sliding window: `window += latencies[i+k-1] - latencies[i-1]`. Compare `window > threshold * k` to avoid float division.",
        ],
        "tests": [
            {"args": [[10, 20, 30, 40, 50], 2, 30]},
            {"args": [[100, 100, 100], 3, 99.9]},
            {"args": [[5, 5, 5], 4, 1], "hidden": True, "why": "k > len(latencies) -> []."},
            {"args": [[50, 50], 1, 50], "hidden": True, "why": "Strictly greater: an average equal to the threshold doesn't alert."},
            {"args": [[1, 2, 3], 1, 0], "hidden": True, "why": "k = 1: every sample is its own window."},
            {"args": [[0, 0, 90, 0, 0], 3, 29], "hidden": True, "why": "Windows are [0..2], [1..3], [2..4]; all average 30."},
            {"args_code": "[[(i * 7919) % 101 for i in range(1000000)], 50000, 50.0]",
             "label": "latency_alerts(<1,000,000 samples>, 50000, 50.0)", "hidden": True,
             "why": "Large input. Recomputing each window is O(n·k); use a running sum."},
        ],
    },
    {
        "id": "py-hop-count",
        "title": "Minimum Router Hops",
        "difficulty": "Medium",
        "category": "Python · Networking",
        "func": "hop_count",
        "description": D("""
            A network topology is given as a list of **bidirectional** links
            `[router_a, router_b]`. Write `hop_count(links, src, dst)` that returns
            the minimum number of hops (links traversed) from `src` to `dst`.

            - `src == dst` -> `0` (even if the router has no links)
            - unreachable or unknown router -> `-1`

            ```
            links = [["A","B"], ["B","C"], ["C","D"], ["D","E"], ["A","E"]]
            hop_count(links, "A", "D") -> 2     # A -> E -> D
            ```

            Topologies can contain cycles and up to ~5,000 routers in a chain.
        """),
        "starter": D("""
            def hop_count(links, src, dst):
                # your code here
                pass
        """),
        "solution": D("""
            from collections import deque

            def hop_count(links, src, dst):
                if src == dst:
                    return 0
                graph = {}
                for a, b in links:
                    graph.setdefault(a, []).append(b)
                    graph.setdefault(b, []).append(a)
                seen = {src}
                queue = deque([(src, 0)])
                while queue:
                    node, dist = queue.popleft()
                    for nxt in graph.get(node, []):
                        if nxt == dst:
                            return dist + 1
                        if nxt not in seen:
                            seen.add(nxt)
                            queue.append((nxt, dist + 1))
                return -1
        """),
        "perf_hint": "Use an iterative BFS with collections.deque. Recursion overflows on long chains.",
        "hints": [
            "Build an adjacency list (dict of lists). Add both directions for each link.",
            "Shortest path in an unweighted graph = **BFS**, not DFS.",
            "Use `collections.deque` and a `seen` set so cycles don't loop forever.",
        ],
        "tests": [
            {"args": [[["A", "B"], ["B", "C"], ["C", "D"]], "A", "D"]},
            {"args": [[["A", "B"], ["B", "C"], ["C", "D"], ["D", "E"], ["A", "E"]], "A", "D"],
             "why": "Need the SHORTEST path (A-E-D = 2). DFS may find A-B-C-D = 3."},
            {"args": [[["A", "B"], ["C", "D"]], "A", "D"], "hidden": True, "why": "Disconnected -> -1."},
            {"args": [[["A", "B"]], "A", "A"], "hidden": True, "why": "src == dst -> 0."},
            {"args": [[["A", "B"]], "A", "Z"], "hidden": True, "why": "Unknown destination -> -1."},
            {"args": [[["B", "A"]], "A", "B"], "hidden": True, "why": "Links are bidirectional."},
            {"args": [[["A", "B"], ["B", "C"], ["C", "A"], ["C", "D"]], "A", "D"], "hidden": True,
             "why": "Graph has a cycle. Track visited nodes."},
            {"args": [[], "X", "X"], "hidden": True, "why": "src == dst with no links -> 0."},
            {"args_code": "[[[f'r{i}', f'r{i+1}'] for i in range(5000)], 'r0', 'r5000']",
             "label": "hop_count(<chain r0-r1-...-r5000>, 'r0', 'r5000')", "hidden": True,
             "why": "Deep recursion hits Python's ~1000 frame limit. Use iterative BFS."},
        ],
    },
    {
        "id": "py-longest-prefix",
        "title": "Longest Prefix Match (Routing Table)",
        "difficulty": "Hard",
        "category": "Python · Networking",
        "func": "longest_prefix_match",
        "description": D("""
            A routing table is a dict mapping CIDR prefixes to next hops. Write
            `longest_prefix_match(routes, ip)` that returns the next hop of the
            **most specific** (longest prefix) route containing `ip`, or `None` if
            no route matches.

            ```
            routes = {
                "0.0.0.0/0":      "isp-gw",
                "10.0.0.0/8":     "core-1",
                "10.20.0.0/16":   "core-2",
                "10.20.30.0/24":  "dist-7",
            }
            longest_prefix_match(routes, "10.20.30.40") -> "dist-7"
            longest_prefix_match(routes, "10.20.99.1")  -> "core-2"
            longest_prefix_match(routes, "8.8.8.8")     -> "isp-gw"
            ```
        """),
        "starter": D("""
            def longest_prefix_match(routes, ip):
                # your code here
                pass
        """),
        "solution": D("""
            def longest_prefix_match(routes, ip):
                def to_int(addr):
                    n = 0
                    for octet in addr.split("."):
                        n = (n << 8) | int(octet)
                    return n

                target = to_int(ip)
                best_len, best_hop = -1, None
                for cidr, hop in routes.items():
                    net, plen = cidr.split("/")
                    plen = int(plen)
                    mask = (0xFFFFFFFF << (32 - plen)) & 0xFFFFFFFF
                    if (target & mask) == (to_int(net) & mask) and plen > best_len:
                        best_len, best_hop = plen, hop
                return best_hop
        """),
        "hints": [
            "A route `net/plen` matches when `ip & mask == net & mask`.",
            "Check every route and keep the matching one with the largest `plen`. Don't return the first match.",
            "`0.0.0.0/0` has mask 0, so it matches every IP (the default route).",
        ],
        "tests": [
            {"args": [{"0.0.0.0/0": "isp-gw", "10.0.0.0/8": "core-1", "10.20.0.0/16": "core-2", "10.20.30.0/24": "dist-7"}, "10.20.30.40"]},
            {"args": [{"0.0.0.0/0": "isp-gw", "10.0.0.0/8": "core-1", "10.20.0.0/16": "core-2", "10.20.30.0/24": "dist-7"}, "10.20.99.1"]},
            {"args": [{"0.0.0.0/0": "isp-gw", "10.0.0.0/8": "core-1", "10.20.0.0/16": "core-2", "10.20.30.0/24": "dist-7"}, "10.99.1.1"], "hidden": True},
            {"args": [{"0.0.0.0/0": "isp-gw", "10.0.0.0/8": "core-1"}, "8.8.8.8"], "hidden": True,
             "why": "0.0.0.0/0 is the default route and matches everything."},
            {"args": [{"10.0.0.0/8": "core-1"}, "192.168.1.1"], "hidden": True, "why": "No match -> None."},
            {"args": [{"10.0.0.0/8": "a", "10.0.0.0/9": "b"}, "10.200.0.1"], "hidden": True,
             "why": "10.0.0.0/9 only covers 10.0-10.127, so 10.200.x falls back to the /8."},
            {"args": [{"192.168.1.0/24": "lan", "192.168.1.5/32": "host-route"}, "192.168.1.5"], "hidden": True,
             "why": "A /32 host route is the most specific."},
            {"args": [{"10.0.0.0/8": "core", "10.20.30.0/24": "dist"}, "10.20.30.1"], "hidden": True,
             "why": "Don't return the first match; return the LONGEST prefix."},
        ],
    },
]


# --------------------------------------------------------------------------
# SQL
# --------------------------------------------------------------------------

SQL_SCHEMA = D("""
    CREATE TABLE sites (
        site_code   TEXT PRIMARY KEY,
        city        TEXT,
        state       TEXT,
        region      TEXT
    );
    CREATE TABLE devices (
        device_id    INTEGER PRIMARY KEY,
        hostname     TEXT,
        site_code    TEXT REFERENCES sites(site_code),
        vendor       TEXT,
        device_type  TEXT,   -- router | switch | firewall
        install_date TEXT    -- YYYY-MM-DD
    );
    CREATE TABLE interfaces (
        interface_id INTEGER PRIMARY KEY,
        device_id    INTEGER REFERENCES devices(device_id),
        name         TEXT,
        speed_mbps   INTEGER,
        status       TEXT    -- up | down | admin-down
    );
    CREATE TABLE incidents (
        incident_id  INTEGER PRIMARY KEY,
        device_id    INTEGER REFERENCES devices(device_id),
        opened_at    TEXT,   -- YYYY-MM-DD HH:MM:SS
        closed_at    TEXT,   -- NULL while still open
        severity     TEXT,   -- critical | major | minor
        category     TEXT    -- hardware | link | config | power
    );
    CREATE TABLE traffic (
        device_id    INTEGER REFERENCES devices(device_id),
        sample_date  TEXT,   -- YYYY-MM-DD
        gb_in        INTEGER,
        gb_out       INTEGER
    );
""")

_SITES = [
    ("DAL1", "Dallas", "TX", "South"),
    ("ATL1", "Atlanta", "GA", "South"),
    ("CHI1", "Chicago", "IL", "Midwest"),
    ("NYC1", "New York", "NY", "Northeast"),
    ("SEA1", "Seattle", "WA", "West"),
    ("LAX1", "Los Angeles", "CA", "West"),
]

_DEVICES = [
    (1, "dal1-core-01", "DAL1", "Cisco", "router", "2021-03-15"),
    (2, "dal1-core-02", "DAL1", "Juniper", "router", "2022-07-01"),
    (3, "dal1-acc-01", "DAL1", "Cisco", "switch", "2023-01-20"),
    (4, "atl1-core-01", "ATL1", "Nokia", "router", "2020-11-05"),
    (5, "atl1-acc-01", "ATL1", "Arista", "switch", "2023-06-10"),
    (6, "chi1-core-01", "CHI1", "Cisco", "router", "2019-09-30"),
    (7, "chi1-fw-01", "CHI1", "Palo Alto", "firewall", "2022-02-14"),
    (8, "nyc1-core-01", "NYC1", "Juniper", "router", "2021-12-01"),
    (9, "nyc1-core-02", "NYC1", "Cisco", "router", "2023-04-18"),
    (10, "nyc1-acc-01", "NYC1", "Arista", "switch", "2024-01-08"),
    (11, "nyc1-fw-01", "NYC1", "Palo Alto", "firewall", "2023-09-22"),
    (12, "sea1-core-01", "SEA1", "Nokia", "router", "2022-05-05"),
    (13, "sea1-acc-01", "SEA1", "Cisco", "switch", "2024-03-03"),
]

_INTERFACES = [
    (1, 1, "ge-0/0/0", 10000, "up"),
    (2, 1, "ge-0/0/1", 10000, "up"),
    (3, 1, "ge-0/0/2", 1000, "down"),
    (4, 2, "xe-0/0/0", 10000, "up"),
    (5, 2, "xe-0/0/1", 10000, "admin-down"),
    (6, 3, "Gi1/0/1", 1000, "up"),
    (7, 3, "Gi1/0/2", 1000, "down"),
    (8, 3, "Gi1/0/3", 1000, "down"),
    (9, 4, "1/1/1", 100000, "up"),
    (10, 4, "1/1/2", 100000, "up"),
    (11, 5, "Et1", 25000, "up"),
    (12, 5, "Et2", 25000, "up"),
    (13, 6, "Te0/1", 10000, "down"),
    (14, 6, "Te0/2", 10000, "up"),
    (15, 7, "eth1/1", 1000, "up"),
    (16, 7, "eth1/2", 1000, "up"),
    (17, 8, "et-0/0/0", 100000, "up"),
    (18, 8, "et-0/0/1", 100000, "down"),
    (19, 9, "Hu0/0/0", 100000, "up"),
    (20, 10, "Et1", 25000, "up"),
    (21, 10, "Et2", 25000, "admin-down"),
    (22, 11, "eth1/1", 10000, "up"),
    (23, 12, "1/1/1", 100000, "up"),
    (24, 12, "1/1/2", 100000, "down"),
    (25, 13, "Gi1/0/1", 1000, "up"),
    (26, 13, "Gi1/0/2", 1000, "up"),
]

_INCIDENTS = [
    (1, 1, "2026-08-01 08:00:00", "2026-08-01 12:30:00", "major", "link"),
    (2, 1, "2026-08-15 22:10:00", "2026-08-16 01:10:00", "critical", "power"),
    (3, 3, "2026-08-03 09:00:00", "2026-08-03 10:00:00", "minor", "config"),
    (4, 3, "2026-09-20 14:00:00", None, "major", "link"),
    (5, 4, "2026-07-11 03:00:00", "2026-07-11 09:00:00", "critical", "hardware"),
    (6, 6, "2026-08-21 10:00:00", None, "critical", "hardware"),
    (7, 6, "2026-09-02 11:00:00", None, "minor", "link"),
    (8, 6, "2026-09-28 16:45:00", None, "critical", "link"),
    (9, 7, "2026-09-05 13:00:00", "2026-09-05 13:45:00", "minor", "config"),
    (10, 8, "2026-08-09 07:30:00", "2026-08-10 07:30:00", "major", "hardware"),
    (11, 8, "2026-09-30 19:00:00", None, "critical", "link"),
    (12, 9, "2026-09-12 05:00:00", "2026-09-12 06:30:00", "minor", "config"),
    (13, 11, "2026-09-25 12:00:00", None, "major", "config"),
    (14, 12, "2026-08-18 00:00:00", "2026-08-18 04:00:00", "major", "power"),
    (15, 13, "2026-09-29 09:15:00", None, "minor", "link"),
    (16, 8, "2026-09-10 10:00:00", "2026-09-10 11:00:00", "minor", "config"),
]


def _traffic_rows():
    base = {"router": 400, "switch": 120, "firewall": 80}
    dates = ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"]
    rows = []
    for dev_id, _, _, _, dtype, _ in _DEVICES:
        for day, date in enumerate(dates):
            gb_in = base[dtype] + (dev_id * 37 + day * 53) % 60
            gb_out = int(base[dtype] * 0.8) + (dev_id * 29 + day * 17) % 45
            rows.append((dev_id, date, gb_in, gb_out))
    return rows


def build_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SQL_SCHEMA)
    conn.executemany("INSERT INTO sites VALUES (?,?,?,?)", _SITES)
    conn.executemany("INSERT INTO devices VALUES (?,?,?,?,?,?)", _DEVICES)
    conn.executemany("INSERT INTO interfaces VALUES (?,?,?,?,?)", _INTERFACES)
    conn.executemany("INSERT INTO incidents VALUES (?,?,?,?,?,?)", _INCIDENTS)
    conn.executemany("INSERT INTO traffic VALUES (?,?,?,?)", _traffic_rows())
    conn.commit()
    return conn


SQL_STARTER = "-- SQLite dialect. Write a single SELECT statement.\nSELECT\n  \nFROM "

SQL_QUESTIONS = [
    {
        "id": "sql-cisco-devices",
        "title": "Cisco Devices by Install Date",
        "difficulty": "Easy",
        "description": D("""
            List the `hostname` and `install_date` of every device whose vendor is
            **Cisco**, ordered by `install_date` (oldest first).

            **Columns:** `hostname`, `install_date`
        """),
        "solution": D("""
            SELECT hostname, install_date
            FROM devices
            WHERE vendor = 'Cisco'
            ORDER BY install_date;
        """),
        "ordered": True,
        "hints": [
            "Filter with `WHERE vendor = 'Cisco'`. String literals use single quotes.",
            "Dates stored as `YYYY-MM-DD` text sort correctly as strings.",
        ],
        "pitfalls": ["String literals in SQL use single quotes; double quotes mean identifiers."],
    },
    {
        "id": "sql-devices-per-site",
        "title": "Device Count per Site",
        "difficulty": "Easy",
        "description": D("""
            Return the number of devices at each site that has at least one
            device. Order by `device_count` descending, then `site_code` ascending.

            **Columns:** `site_code`, `device_count`
        """),
        "solution": D("""
            SELECT site_code, COUNT(*) AS device_count
            FROM devices
            GROUP BY site_code
            ORDER BY device_count DESC, site_code;
        """),
        "ordered": True,
        "hints": [
            "`GROUP BY site_code` with `COUNT(*)`.",
            "You can sort by multiple columns: `ORDER BY device_count DESC, site_code`.",
        ],
        "pitfalls": ["Every non-aggregated column in SELECT should appear in GROUP BY."],
    },
    {
        "id": "sql-interfaces-not-up",
        "title": "Interfaces That Aren't Up",
        "difficulty": "Easy",
        "description": D("""
            List every interface whose status is anything other than `up`, along
            with the device hostname. Order by `hostname`, then interface name.

            **Columns:** `hostname`, `interface`, `status`
        """),
        "solution": D("""
            SELECT d.hostname, i.name AS interface, i.status
            FROM interfaces i
            JOIN devices d ON d.device_id = i.device_id
            WHERE i.status <> 'up'
            ORDER BY d.hostname, i.name;
        """),
        "ordered": True,
        "hints": [
            "JOIN `interfaces` to `devices` on `device_id`.",
            "There are two non-up statuses: `down` **and** `admin-down`. Use `<> 'up'`.",
        ],
        "pitfalls": [
            "Filtering `status = 'down'` misses `admin-down` interfaces.",
            "Alias `i.name AS interface` to match the expected column name.",
        ],
    },
    {
        "id": "sql-all-sites-count",
        "title": "Every Site's Device Count (Including Zero)",
        "difficulty": "Medium",
        "description": D("""
            List **every** site with its city and number of devices, including
            sites that have no devices (they should show `0`). Order by
            `device_count` descending, then `site_code`.

            **Columns:** `site_code`, `city`, `device_count`
        """),
        "solution": D("""
            SELECT s.site_code, s.city, COUNT(d.device_id) AS device_count
            FROM sites s
            LEFT JOIN devices d ON d.site_code = s.site_code
            GROUP BY s.site_code, s.city
            ORDER BY device_count DESC, s.site_code;
        """),
        "ordered": True,
        "hints": [
            "An INNER JOIN drops sites with no devices. Start FROM `sites` and LEFT JOIN `devices`.",
            "`COUNT(*)` counts the NULL-filled row as 1. Use `COUNT(d.device_id)` to count only real matches.",
        ],
        "pitfalls": [
            "COUNT(*) after a LEFT JOIN returns 1 (not 0) for sites without devices; COUNT(column) skips NULLs.",
            "INNER JOIN removes sites with zero devices (LAX1).",
        ],
    },
    {
        "id": "sql-open-incidents",
        "title": "Sites with Multiple Open Incidents",
        "difficulty": "Medium",
        "description": D("""
            An incident is **open** when `closed_at` is NULL. Find sites with
            **at least 2** open incidents. Order by `open_incidents` descending,
            then `site_code`.

            **Columns:** `site_code`, `city`, `open_incidents`
        """),
        "solution": D("""
            SELECT s.site_code, s.city, COUNT(*) AS open_incidents
            FROM incidents i
            JOIN devices d ON d.device_id = i.device_id
            JOIN sites s ON s.site_code = d.site_code
            WHERE i.closed_at IS NULL
            GROUP BY s.site_code, s.city
            HAVING COUNT(*) >= 2
            ORDER BY open_incidents DESC, s.site_code;
        """),
        "ordered": True,
        "hints": [
            "Incidents link to sites via devices: incidents -> devices -> sites.",
            "Use `IS NULL`. `= NULL` is never true.",
            "Filter on an aggregate with `HAVING`, not `WHERE`.",
        ],
        "pitfalls": [
            "`closed_at = NULL` always evaluates to NULL (not true). Use `IS NULL`.",
            "`WHERE COUNT(*) >= 2` is an error. Aggregates are filtered with HAVING.",
        ],
    },
    {
        "id": "sql-no-incidents",
        "title": "Devices with No Incidents",
        "difficulty": "Medium",
        "description": D("""
            List devices that have **never** had an incident. Order by `hostname`.

            **Columns:** `hostname`, `vendor`
        """),
        "solution": D("""
            SELECT d.hostname, d.vendor
            FROM devices d
            LEFT JOIN incidents i ON i.device_id = d.device_id
            WHERE i.incident_id IS NULL
            ORDER BY d.hostname;
        """),
        "ordered": True,
        "hints": [
            "Anti-join pattern: `LEFT JOIN ... WHERE right_table.id IS NULL`.",
            "Alternatives: `WHERE device_id NOT IN (SELECT device_id FROM incidents)` or `NOT EXISTS (...)`.",
        ],
        "pitfalls": ["Putting the IS NULL condition in the ON clause instead of WHERE returns every device."],
    },
    {
        "id": "sql-incidents-september",
        "title": "September Incidents by Category",
        "difficulty": "Medium",
        "description": D("""
            Count incidents **opened** in September 2026, grouped by category.
            Order by `incident_count` descending, then `category`.

            **Columns:** `category`, `incident_count`
        """),
        "solution": D("""
            SELECT category, COUNT(*) AS incident_count
            FROM incidents
            WHERE opened_at >= '2026-09-01' AND opened_at < '2026-10-01'
            GROUP BY category
            ORDER BY incident_count DESC, category;
        """),
        "ordered": True,
        "hints": [
            "Timestamps are text `YYYY-MM-DD HH:MM:SS`, so range comparisons work as strings.",
            "Options: `opened_at >= '2026-09-01' AND opened_at < '2026-10-01'`, or `strftime('%Y-%m', opened_at) = '2026-09'`.",
        ],
        "pitfalls": [
            "`BETWEEN '2026-09-01' AND '2026-09-30'` misses anything on Sep 30 after 00:00:00 (e.g. '2026-09-30 19:00:00' > '2026-09-30').",
        ],
    },
    {
        "id": "sql-legacy-critical",
        "title": "Legacy Devices with Critical Incidents",
        "difficulty": "Medium",
        "description": D("""
            List devices installed **before 2022** that have had **at least one**
            `critical` incident. Each device should appear only once. Order by
            `install_date`.

            **Columns:** `hostname`, `install_date`
        """),
        "solution": D("""
            SELECT DISTINCT d.hostname, d.install_date
            FROM devices d
            JOIN incidents i ON i.device_id = d.device_id
            WHERE d.install_date < '2022-01-01'
              AND i.severity = 'critical'
            ORDER BY d.install_date;
        """),
        "ordered": True,
        "hints": [
            "Some devices have *multiple* critical incidents, so a plain JOIN duplicates rows.",
            "Use `SELECT DISTINCT`, or `WHERE EXISTS (SELECT 1 FROM incidents ...)`.",
        ],
        "pitfalls": ["JOIN produces one row per matching incident. Use DISTINCT or EXISTS to dedupe."],
    },
    {
        "id": "sql-resolution-time",
        "title": "Average Resolution Time by Severity",
        "difficulty": "Medium",
        "description": D("""
            For **closed** incidents only, compute the average time to resolve in
            **hours**, rounded to 2 decimals, per severity. Also include how many
            closed incidents each severity has. Order by `avg_hours` descending.

            **Columns:** `severity`, `avg_hours`, `closed_count`

            *SQLite tip:* `julianday(ts)` returns days as a float.
        """),
        "solution": D("""
            SELECT severity,
                   ROUND(AVG((julianday(closed_at) - julianday(opened_at)) * 24), 2) AS avg_hours,
                   COUNT(*) AS closed_count
            FROM incidents
            WHERE closed_at IS NOT NULL
            GROUP BY severity
            ORDER BY avg_hours DESC;
        """),
        "ordered": True,
        "hints": [
            "`(julianday(closed_at) - julianday(opened_at)) * 24` = duration in hours.",
            "Filter `closed_at IS NOT NULL` so open incidents don't affect the average.",
            "Wrap with `ROUND(AVG(...), 2)`.",
        ],
        "pitfalls": [
            "AVG ignores NULLs, but COUNT(*) does not. Without the closed filter, closed_count is wrong.",
            "In MySQL you'd use TIMESTAMPDIFF; in PostgreSQL EXTRACT(EPOCH FROM ...). Know your dialect.",
        ],
    },
    {
        "id": "sql-traffic-region",
        "title": "Total Traffic per Region",
        "difficulty": "Medium",
        "description": D("""
            Compute total traffic (`gb_in + gb_out`) per region across all
            samples. Order by `total_gb` descending.

            **Columns:** `region`, `total_gb`
        """),
        "solution": D("""
            SELECT s.region, SUM(t.gb_in + t.gb_out) AS total_gb
            FROM traffic t
            JOIN devices d ON d.device_id = t.device_id
            JOIN sites s ON s.site_code = d.site_code
            GROUP BY s.region
            ORDER BY total_gb DESC;
        """),
        "ordered": True,
        "hints": [
            "Three-table join: traffic -> devices -> sites.",
            "`SUM(gb_in + gb_out)` or `SUM(gb_in) + SUM(gb_out)` both work.",
        ],
        "pitfalls": ["Grouping by site_code instead of region gives one row per site."],
    },
    {
        "id": "sql-down-pct",
        "title": "Interface Down % by Device Type",
        "difficulty": "Hard",
        "description": D("""
            For each `device_type`, return the total number of interfaces and the
            percentage whose status is exactly `down`, rounded to 1 decimal.
            Order by `down_pct` descending, then `device_type`.

            **Columns:** `device_type`, `total_interfaces`, `down_pct`
        """),
        "solution": D("""
            SELECT d.device_type,
                   COUNT(*) AS total_interfaces,
                   ROUND(100.0 * SUM(CASE WHEN i.status = 'down' THEN 1 ELSE 0 END) / COUNT(*), 1) AS down_pct
            FROM interfaces i
            JOIN devices d ON d.device_id = i.device_id
            GROUP BY d.device_type
            ORDER BY down_pct DESC, d.device_type;
        """),
        "ordered": True,
        "hints": [
            "Conditional aggregation: `SUM(CASE WHEN status = 'down' THEN 1 ELSE 0 END)`.",
            "Integer / integer = integer in SQLite (and SQL Server). Multiply by `100.0` first.",
        ],
        "pitfalls": [
            "Integer division: 2 / 9 = 0 in SQLite. Use 100.0 * ... to force floating point.",
            "Only 'down' counts here, not 'admin-down'.",
        ],
    },
    {
        "id": "sql-above-avg-traffic",
        "title": "Devices Above Average Traffic",
        "difficulty": "Hard",
        "description": D("""
            Each device's total traffic is the sum of `gb_in + gb_out` over all of
            its samples. List devices whose total is **greater than the average
            device total**. Order by `total_gb` descending.

            **Columns:** `hostname`, `total_gb`
        """),
        "solution": D("""
            WITH totals AS (
                SELECT d.hostname, SUM(t.gb_in + t.gb_out) AS total_gb
                FROM devices d
                JOIN traffic t ON t.device_id = d.device_id
                GROUP BY d.device_id, d.hostname
            )
            SELECT hostname, total_gb
            FROM totals
            WHERE total_gb > (SELECT AVG(total_gb) FROM totals)
            ORDER BY total_gb DESC;
        """),
        "ordered": True,
        "hints": [
            "First compute per-device totals (a CTE: `WITH totals AS (...)`).",
            "Then compare against `(SELECT AVG(total_gb) FROM totals)`. That's the average of *device totals*, not of raw samples.",
        ],
        "pitfalls": [
            "AVG(gb_in + gb_out) over raw traffic rows is the per-sample average, not the per-device average.",
        ],
    },
    {
        "id": "sql-top-device-per-site",
        "title": "Busiest Device per Site",
        "difficulty": "Hard",
        "description": D("""
            For each site, return the single device with the highest total traffic
            (`gb_in + gb_out` summed over all samples). Break ties by lower
            `device_id`. Order by `site_code`.

            **Columns:** `site_code`, `hostname`, `total_gb`
        """),
        "solution": D("""
            WITH totals AS (
                SELECT d.site_code, d.device_id, d.hostname,
                       SUM(t.gb_in + t.gb_out) AS total_gb
                FROM devices d
                JOIN traffic t ON t.device_id = d.device_id
                GROUP BY d.device_id
            ),
            ranked AS (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY site_code ORDER BY total_gb DESC, device_id
                ) AS rn
                FROM totals
            )
            SELECT site_code, hostname, total_gb
            FROM ranked
            WHERE rn = 1
            ORDER BY site_code;
        """),
        "ordered": True,
        "hints": [
            "Step 1: per-device totals in a CTE.",
            "Step 2: `ROW_NUMBER() OVER (PARTITION BY site_code ORDER BY total_gb DESC, device_id)`.",
            "Step 3: keep `rn = 1`. Window functions can't go in WHERE directly, so wrap them in another CTE/subquery.",
        ],
        "pitfalls": [
            "SELECT hostname, MAX(total) ... GROUP BY site works by accident in SQLite but fails in most databases. Learn the window-function way.",
            "Window functions can't be referenced in WHERE of the same SELECT.",
        ],
    },
    {
        "id": "sql-day-over-day",
        "title": "Day-over-Day Inbound Change",
        "difficulty": "Hard",
        "description": D("""
            For device `nyc1-core-01`, show each day's `gb_in` and the change from
            the previous day (`NULL` for the first day). Order by `sample_date`.

            **Columns:** `sample_date`, `gb_in`, `change_gb`
        """),
        "solution": D("""
            SELECT t.sample_date,
                   t.gb_in,
                   t.gb_in - LAG(t.gb_in) OVER (ORDER BY t.sample_date) AS change_gb
            FROM traffic t
            JOIN devices d ON d.device_id = t.device_id
            WHERE d.hostname = 'nyc1-core-01'
            ORDER BY t.sample_date;
        """),
        "ordered": True,
        "hints": [
            "`LAG(col) OVER (ORDER BY sample_date)` gives the previous row's value.",
            "Filter the device by joining to `devices` on hostname (don't hard-code the id).",
        ],
        "pitfalls": ["Self-joining on date - 1 day works but is fragile. LAG is the idiomatic answer."],
    },
]

for q in SQL_QUESTIONS:
    q["category"] = "SQL"
    q["starter"] = SQL_STARTER


# --------------------------------------------------------------------------
# CONCEPTS (multiple choice)
# --------------------------------------------------------------------------

MCQ_QUESTIONS = [
    {
        "id": "mcq-osi-router",
        "title": "OSI Layer of a Router",
        "difficulty": "Easy",
        "description": "At which OSI layer does a router primarily make forwarding decisions?",
        "options": ["Layer 1 - Physical", "Layer 2 - Data Link", "Layer 3 - Network", "Layer 4 - Transport"],
        "answer": 2,
        "explanation": "Routers forward packets based on IP (Layer 3) addresses. Switches forward frames using MAC addresses (Layer 2).",
    },
    {
        "id": "mcq-slash27",
        "title": "Hosts in a /27",
        "difficulty": "Easy",
        "description": "How many usable host addresses are in a /27 subnet?",
        "options": ["32", "30", "62", "14"],
        "answer": 1,
        "explanation": "2^(32-27) = 32 addresses, minus network and broadcast = 30.",
    },
    {
        "id": "mcq-mask26",
        "title": "Subnet Mask for /26",
        "difficulty": "Easy",
        "description": "What is the dotted-decimal subnet mask for a /26?",
        "options": ["255.255.255.128", "255.255.255.192", "255.255.255.224", "255.255.255.240"],
        "answer": 1,
        "explanation": "26 bits = 24 + 2. The last octet is 11000000 = 128 + 64 = 192.",
    },
    {
        "id": "mcq-broadcast",
        "title": "Broadcast Address",
        "difficulty": "Medium",
        "description": "What is the broadcast address of 192.168.10.70/26?",
        "options": ["192.168.10.63", "192.168.10.127", "192.168.10.255", "192.168.10.71"],
        "answer": 1,
        "explanation": "A /26 has block size 64: .0, .64, .128, .192. Address .70 is in .64-.127, so the broadcast is .127.",
    },
    {
        "id": "mcq-private",
        "title": "Private IPv4 Ranges",
        "difficulty": "Easy",
        "description": "Which of these is **NOT** an RFC 1918 private range?",
        "options": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "172.32.0.0/16"],
        "answer": 3,
        "explanation": "172.16.0.0/12 covers 172.16.0.0-172.31.255.255. 172.32.x.x is public.",
    },
    {
        "id": "mcq-arp",
        "title": "Resolving IP to MAC",
        "difficulty": "Easy",
        "description": "Which protocol resolves an IPv4 address to a MAC address on a local network?",
        "options": ["DNS", "DHCP", "ARP", "ICMP"],
        "answer": 2,
        "explanation": "ARP broadcasts 'who has 10.0.0.5?' and the owner replies with its MAC. (IPv6 uses NDP instead.)",
    },
    {
        "id": "mcq-tcp-udp",
        "title": "TCP vs UDP",
        "difficulty": "Easy",
        "description": "Which statement is TRUE?",
        "options": [
            "UDP guarantees in-order delivery",
            "TCP uses a three-way handshake and provides reliable, ordered delivery",
            "TCP is connectionless",
            "UDP retransmits lost packets automatically",
        ],
        "answer": 1,
        "explanation": "TCP: SYN, SYN-ACK, ACK, with sequencing and retransmission. UDP is connectionless and best-effort (used by DNS queries, VoIP, streaming).",
    },
    {
        "id": "mcq-ports",
        "title": "Well-Known Ports",
        "difficulty": "Easy",
        "description": "Which pairing of protocol to default port is correct?",
        "options": ["SSH - 23", "DNS - 53", "HTTPS - 8080", "BGP - 520"],
        "answer": 1,
        "explanation": "DNS = 53 (UDP & TCP). SSH = 22, Telnet = 23, HTTPS = 443, BGP = TCP 179, RIP = UDP 520.",
    },
    {
        "id": "mcq-bgp",
        "title": "BGP Classification",
        "difficulty": "Medium",
        "description": "BGP is best described as a:",
        "options": [
            "Link-state interior gateway protocol",
            "Distance-vector interior gateway protocol",
            "Path-vector exterior gateway protocol",
            "Layer 2 loop-prevention protocol",
        ],
        "answer": 2,
        "explanation": "BGP exchanges AS paths between autonomous systems (EGP, path-vector). OSPF/IS-IS are link-state IGPs, and STP prevents L2 loops.",
    },
    {
        "id": "mcq-ospf",
        "title": "OSPF Metric",
        "difficulty": "Medium",
        "description": "What does OSPF use as its metric to choose the best path?",
        "options": ["Hop count", "Cost, derived from interface bandwidth", "AS path length", "Round-trip latency"],
        "answer": 1,
        "explanation": "OSPF cost = reference bandwidth / interface bandwidth. RIP uses hop count; BGP prefers shorter AS paths (among other attributes).",
    },
    {
        "id": "mcq-vlan",
        "title": "Purpose of VLANs",
        "difficulty": "Easy",
        "description": "What is the primary function of a VLAN?",
        "options": [
            "Encrypt traffic between switches",
            "Split one physical switch into multiple Layer 2 broadcast domains",
            "Translate private IPs to public IPs",
            "Assign IP addresses to hosts",
        ],
        "answer": 1,
        "explanation": "VLANs segment broadcast domains at Layer 2. Traffic between VLANs needs a router or L3 switch. NAT translates addresses, DHCP assigns them.",
    },
    {
        "id": "mcq-ipv6",
        "title": "IPv6 Address Size",
        "difficulty": "Easy",
        "description": "How many bits are in an IPv6 address?",
        "options": ["32", "64", "128", "256"],
        "answer": 2,
        "explanation": "IPv6 addresses are 128 bits, written as 8 groups of 4 hex digits (e.g. 2001:db8::1).",
    },
    {
        "id": "mcq-traceroute",
        "title": "How Traceroute Works",
        "difficulty": "Medium",
        "description": "How does traceroute discover each hop along a path?",
        "options": [
            "It queries each router's routing table via SNMP",
            "It sends packets with increasing TTL values and records ICMP Time Exceeded replies",
            "It uses ARP requests to each router",
            "It reads the BGP AS path",
        ],
        "answer": 1,
        "explanation": "TTL=1 expires at hop 1, TTL=2 at hop 2, etc. Each router that drops the packet sends back ICMP Time Exceeded, revealing its address.",
    },
    {
        "id": "mcq-having",
        "title": "SQL: Filtering Aggregates",
        "difficulty": "Easy",
        "description": "Which SQL clause filters rows **after** GROUP BY aggregation?",
        "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
        "answer": 1,
        "explanation": "WHERE filters rows before grouping; HAVING filters groups after aggregation (e.g. HAVING COUNT(*) > 2).",
    },
    {
        "id": "mcq-left-join",
        "title": "SQL: LEFT JOIN Semantics",
        "difficulty": "Easy",
        "description": "What does `A LEFT JOIN B` return?",
        "options": [
            "Only rows that match in both A and B",
            "All rows from A, with matching B columns or NULLs where there's no match",
            "All rows from B, with NULLs for unmatched A",
            "Every combination of A and B rows",
        ],
        "answer": 1,
        "explanation": "LEFT JOIN keeps every row from the left table. Option 1 is INNER JOIN, option 3 is RIGHT JOIN, and option 4 is CROSS JOIN.",
    },
    {
        "id": "mcq-dict-complexity",
        "title": "Python: Dict Lookup Complexity",
        "difficulty": "Easy",
        "description": "What is the average time complexity of `key in my_dict` in Python?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "answer": 0,
        "explanation": "Dicts and sets are hash tables: average O(1) membership. `x in my_list` is O(n). This matters for performance tests!",
    },
    {
        "id": "mcq-nat",
        "title": "Purpose of NAT",
        "difficulty": "Easy",
        "description": "What problem does NAT (specifically PAT/overload) primarily solve?",
        "options": [
            "It lets many private hosts share one public IPv4 address",
            "It encrypts traffic leaving the network",
            "It prevents routing loops",
            "It assigns MAC addresses",
        ],
        "answer": 0,
        "explanation": "PAT maps many inside private addresses to one public IP using unique source ports, conserving IPv4 space.",
    },
    {
        "id": "mcq-dhcp",
        "title": "DHCP Process",
        "difficulty": "Medium",
        "description": "What is the correct order of the DHCP lease process (DORA)?",
        "options": [
            "Discover, Offer, Request, Acknowledge",
            "Discover, Request, Offer, Acknowledge",
            "Offer, Discover, Acknowledge, Request",
            "Request, Offer, Discover, Acknowledge",
        ],
        "answer": 0,
        "explanation": "The client broadcasts Discover, the server sends an Offer, the client sends a Request, and the server Acknowledges.",
    },
]

for q in MCQ_QUESTIONS:
    q["category"] = "Concepts"


# --------------------------------------------------------------------------

for q in PYTHON_QUESTIONS:
    q["type"] = "python"
for q in SQL_QUESTIONS:
    q["type"] = "sql"
for q in MCQ_QUESTIONS:
    q["type"] = "mcq"

ALL_QUESTIONS = PYTHON_QUESTIONS + SQL_QUESTIONS + MCQ_QUESTIONS
BY_ID = {q["id"]: q for q in ALL_QUESTIONS}
