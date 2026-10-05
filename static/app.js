const $ = (sel) => document.querySelector(sel);
const LS = {
  get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
};

const state = {
  questions: [],
  current: null,
  filter: "all",
  status: LS.get("tdp_status", {}),
  hints: LS.get("tdp_hints", {}),
  mcqChoice: null,
  schema: null,
  timerStart: Date.now(),
};

let editor = null;

// ---------------------------------------------------------------- helpers

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function md(src) {
  const blocks = [];
  src = src.replace(/```\w*\n([\s\S]*?)```/g, (_, code) => {
    blocks.push(`<pre><code>${esc(code.replace(/\n$/, ""))}</code></pre>`);
    return `\u0000${blocks.length - 1}\u0000`;
  });
  const inline = (s) => esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|\W)\*([^*]+)\*(?=\W|$)/g, "$1<em>$2</em>");
  const out = [];
  for (const para of src.split(/\n\s*\n/)) {
    const lines = para.trim().split("\n");
    if (!lines[0]) continue;
    if (/^\u0000\d+\u0000$/.test(lines[0]) && lines.length === 1) { out.push(lines[0]); continue; }
    const listStart = lines.findIndex((l) => /^\s*- /.test(l));
    if (listStart >= 0) {
      const head = lines.slice(0, listStart);
      const items = [];
      for (const l of lines.slice(listStart)) {
        if (/^\s*- /.test(l)) items.push(l.replace(/^\s*- /, ""));
        else if (items.length) items[items.length - 1] += " " + l.trim();
      }
      if (head.length) out.push(`<p>${head.map(inline).join("<br>")}</p>`);
      out.push(`<ul>${items.map((i) => `<li>${inline(i)}</li>`).join("")}</ul>`);
      continue;
    }
    out.push(`<p>${lines.map(inline).join(" ")}</p>`);
  }
  return out.join("").replace(/\u0000(\d+)\u0000/g, (_, i) => blocks[+i]);
}

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  return res.json();
}

function setStatus(id, s) {
  if (state.status[id] === "solved" && s !== "solved") return;
  state.status[id] = s;
  LS.set("tdp_status", state.status);
  renderSidebar();
  renderProgress();
}

function table(cols, rows, limit = 200) {
  if (!cols || !cols.length) return `<div class="notes">(no columns)</div>`;
  const body = rows.slice(0, limit).map((r) =>
    `<tr>${r.map((v) => v === null ? `<td class="null">NULL</td>` : `<td>${esc(v)}</td>`).join("")}</tr>`).join("");
  return `<div class="scroll-x"><table class="result"><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function pointersBlock(list, title = "Pointers") {
  if (!list || !list.length) return "";
  return `<div class="pointers"><h4>💡 ${title}</h4><ul>${list.map((p) => `<li>${md(p).replace(/^<p>|<\/p>$/g, "")}</li>`).join("")}</ul></div>`;
}

// ---------------------------------------------------------------- render

function renderSidebar() {
  const groups = [["python", "Python: Coding & Data"], ["sql", "SQL: Network Inventory DB"], ["mcq", "Concepts: Networking & CS"]];
  const html = [];
  for (const [type, label] of groups) {
    if (state.filter !== "all" && state.filter !== type) continue;
    const qs = state.questions.filter((q) => q.type === type);
    html.push(`<div class="group-title">${label} (${qs.filter((q) => state.status[q.id] === "solved").length}/${qs.length})</div>`);
    for (const q of qs) {
      const st = state.status[q.id] || "";
      html.push(`<div class="q-item ${state.current?.id === q.id ? "active" : ""}" data-id="${q.id}">
        <span class="dot ${st}"></span><span class="name">${esc(q.title)}</span><span class="diff ${q.difficulty}">${q.difficulty}</span></div>`);
    }
  }
  $("#sidebar").innerHTML = html.join("");
  document.querySelectorAll(".q-item").forEach((el) => el.addEventListener("click", () => select(el.dataset.id)));
}

function renderProgress() {
  const solved = state.questions.filter((q) => state.status[q.id] === "solved").length;
  $("#progress").textContent = `Solved ${solved}/${state.questions.length}`;
}

function renderSchema() {
  if (!state.schema) return;
  $("#schemaContent").innerHTML = state.schema.tables.map((t) => `
    <div class="schema-table">
      <h4>${t.name}</h4>
      <div class="cols">${t.columns.map((c) => `${c.name} <span style="opacity:.6">${c.type}</span>`).join(" · ")}</div>
      ${table(t.columns.map((c) => c.name), t.rows, 60)}
    </div>`).join("");
}

function renderHints() {
  const q = state.current;
  const shown = state.hints[q.id] || 0;
  $("#hints").innerHTML = q.hints.slice(0, shown).map((h) => `<li>${md(h).replace(/^<p>|<\/p>$/g, "")}</li>`).join("");
  $("#hintCount").textContent = `${shown}/${q.hints.length}`;
  $("#hintBtn").disabled = shown >= q.hints.length;
}

function select(id) {
  saveCode();
  const q = state.questions.find((x) => x.id === id);
  state.current = q;
  state.mcqChoice = null;
  state.timerStart = Date.now();
  location.hash = id;

  $("#qTitle").textContent = q.title;
  const extra = q.type === "python" ? ` · ${q.sample_count} sample + ${q.test_count - q.sample_count} hidden tests` : "";
  $("#qMeta").innerHTML = `<span class="diff ${q.difficulty}">${q.difficulty}</span><span>${esc(q.category)}${extra}</span>`;
  $("#qDesc").innerHTML = md(q.description);
  $("#schemaBox").classList.toggle("hidden", q.type !== "sql");
  if (q.type === "sql") $("#schemaBox").open = false;
  $("#hintBox").classList.toggle("hidden", !q.hints);
  $("#solutionBox").classList.toggle("hidden", q.type === "mcq");
  $("#solution").classList.add("hidden");
  $("#solutionBtn").textContent = "Show solution";
  if (q.hints) renderHints();

  const isMcq = q.type === "mcq";
  $("#editorWrap").classList.toggle("hidden", isMcq);
  $("#mcqWrap").classList.toggle("hidden", !isMcq);
  $("#runBtn").classList.toggle("hidden", isMcq);
  $("#submitBtn").textContent = isMcq ? "Check answer" : "Submit";

  if (isMcq) {
    renderMcq();
  } else {
    $("#langLabel").textContent = q.type === "sql" ? "SQLite" : "Python 3";
    $("#runBtn").textContent = q.type === "sql" ? "Run query" : "Run samples";
    const code = localStorage.getItem("tdp_code_" + q.id) ?? q.starter;
    if (editor.setOption) {
      editor.setOption("mode", q.type === "sql" ? "text/x-sqlite" : "python");
      editor.setValue(code);
      editor.clearHistory();
      setTimeout(() => { editor.refresh(); editor.focus(); }, 0);
    } else {
      editor.setValue(code);
    }
  }
  $("#console").innerHTML = `<div class="console-empty">${isMcq ? "Pick an answer and click Check answer." :
    q.type === "sql" ? "Run query shows your output without grading. Submit compares it to the expected result." :
    "Run samples executes the visible examples. Submit runs every test, including hidden edge cases."}</div>`;
  renderSidebar();
}

function renderMcq(result) {
  const q = state.current;
  $("#mcqOptions").innerHTML = `<p style="margin-top:0">${md(q.description).replace(/^<p>|<\/p>$/g, "")}</p>` +
    q.options.map((opt, i) => {
      let cls = state.mcqChoice === i ? "selected" : "";
      if (result) cls = i === result.answer ? "correct" : (i === state.mcqChoice ? "wrong" : "");
      return `<div class="mcq-option ${cls}" data-i="${i}"><span class="letter">${"ABCD"[i]}</span><span>${esc(opt)}</span></div>`;
    }).join("");
  document.querySelectorAll(".mcq-option").forEach((el) => el.addEventListener("click", () => {
    state.mcqChoice = +el.dataset.i;
    renderMcq();
  }));
}

// ---------------------------------------------------------------- results

function renderPythonResult(r, mode) {
  const out = [];
  if (r.status === "error") {
    out.push(`<div class="verdict error">⚠ ${r.compile_error ? esc(r.compile_error.error_type) : "Error"}</div>`);
    out.push(pointersBlock(r.pointers));
    if (r.compile_error) {
      const ce = r.compile_error;
      out.push(`<div class="err">${esc(ce.message)}${ce.line ? `\nline ${ce.line}: ${esc(ce.text)}` : ""}${(ce.traceback || []).map((t) => "\n  " + esc(t)).join("")}</div>`);
    }
    return out.join("");
  }
  const pass = r.status === "passed";
  out.push(`<div class="verdict ${pass ? "pass" : "fail"}">${pass ? "✔" : "✘"} ${r.passed}/${r.total} tests passed${mode === "submit" ? (pass ? " · Accepted!" : "") : " (samples)"}</div>`);
  out.push(pointersBlock(r.pointers));
  if (r.module_stdout) out.push(`<div class="subhead">stdout (module level)</div><div class="kv"><span></span><span class="v">${esc(r.module_stdout)}</span></div>`);
  for (const t of r.tests) {
    const cls = t.skipped ? "skip" : t.passed ? "pass" : "fail";
    const icon = t.skipped ? "–" : t.passed ? "✔" : "✘";
    const label = t.timeout ? "Timed out" : t.skipped ? "Not run" : t.passed ? "Passed" : "Failed";
    const body = [];
    if (t.input) body.push(`<span class="k">Input</span><span class="v">${esc(t.input)}</span>`);
    if (t.expected !== undefined) body.push(`<span class="k">Expected</span><span class="v">${esc(t.expected)}</span>`);
    if (t.got !== undefined) body.push(`<span class="k">Got</span><span class="v">${esc(t.got)}</span>`);
    if (t.error_type) body.push(`<span class="k">Error</span><span class="v err">${esc(t.error_type)}: ${esc(t.error)}${(t.traceback || []).map((l) => "\n  " + esc(l)).join("")}</span>`);
    if (t.stdout) body.push(`<span class="k">stdout</span><span class="v">${esc(t.stdout)}</span>`);
    out.push(`<details class="test ${cls}" ${!t.passed && !t.skipped ? "open" : ""}>
      <summary><span class="icon">${icon}</span> Test ${t.index + 1}: ${label} ${t.hidden ? `<span class="tag">hidden</span>` : ""}
      ${t.time_ms !== undefined ? `<span class="ms">${t.time_ms} ms</span>` : ""}</summary>
      <div class="test-body"><div class="kv">${body.join("")}</div>${t.why ? `<div class="why">↳ ${esc(t.why)}</div>` : ""}</div></details>`);
  }
  return out.join("");
}

function renderSqlResult(r, mode) {
  const out = [];
  if (r.status === "error") {
    out.push(`<div class="verdict error">⚠ SQL error</div><div class="err">${esc(r.error)}</div><br>`);
    out.push(pointersBlock(r.pointers));
    return out.join("");
  }
  if (mode === "submit") {
    const pass = r.status === "passed";
    out.push(`<div class="verdict ${pass ? "pass" : "fail"}">${pass ? "✔ Accepted! Output matches." : "✘ Wrong answer"}</div>`);
    out.push(pointersBlock(r.pointers));
    if (r.notes?.length) out.push(`<div class="notes">${r.notes.map(esc).join("<br>")}</div>`);
  }
  out.push(`<div class="subhead">Your output · ${r.row_count} row(s)${r.row_count > r.rows.length ? ` (showing ${r.rows.length})` : ""}</div>`);
  out.push(table(r.columns, r.rows));
  if (mode === "submit" && r.status !== "passed") {
    out.push(`<details><summary class="subhead" style="cursor:pointer">Show expected output (${r.expected_rows.length} rows)</summary>${table(r.expected_columns, r.expected_rows)}</details>`);
  }
  return out.join("");
}

// ---------------------------------------------------------------- actions

function saveCode() {
  const q = state.current;
  if (!q || q.type === "mcq") return;
  const code = editor.getValue();
  if (code !== q.starter) localStorage.setItem("tdp_code_" + q.id, code);
}

let busy = false;
async function execute(mode) {
  const q = state.current;
  if (!q || busy) return;
  busy = true;
  $("#busy").classList.remove("hidden");
  $("#runBtn").disabled = $("#submitBtn").disabled = true;
  try {
    if (q.type === "mcq") {
      if (state.mcqChoice === null) { $("#console").innerHTML = `<div class="console-empty">Select an option first.</div>`; return; }
      const r = await api("/api/mcq", { id: q.id, choice: state.mcqChoice });
      renderMcq(r);
      $("#console").innerHTML = `<div class="verdict ${r.correct ? "pass" : "fail"}">${r.correct ? "✔ Correct!" : `✘ Not quite. Answer: ${"ABCD"[r.answer]}`}</div>
        <div class="explain">${md(r.explanation)}</div>`;
      setStatus(q.id, r.correct ? "solved" : "attempted");
      return;
    }
    saveCode();
    const code = editor.getValue();
    if (q.type === "python") {
      const r = await api("/api/run", { id: q.id, code, mode });
      $("#console").innerHTML = renderPythonResult(r, mode);
      setStatus(q.id, r.status === "passed" && mode === "submit" ? "solved" : "attempted");
    } else {
      const r = mode === "submit" ? await api("/api/sql/submit", { id: q.id, code }) : await api("/api/sql/run", { code });
      $("#console").innerHTML = renderSqlResult(r, mode);
      setStatus(q.id, r.status === "passed" ? "solved" : "attempted");
    }
  } catch (e) {
    $("#console").innerHTML = `<div class="verdict error">⚠ Could not reach the server. Is server.py still running?</div><div class="err">${esc(e)}</div>`;
  } finally {
    busy = false;
    $("#busy").classList.add("hidden");
    $("#runBtn").disabled = $("#submitBtn").disabled = false;
    $("#console").scrollTop = 0;
  }
}

// ---------------------------------------------------------------- init

function initEditor() {
  const ta = $("#editor");
  const keys = {
    "Cmd-Enter": () => execute("sample"), "Ctrl-Enter": () => execute("sample"),
    "Shift-Cmd-Enter": () => execute("submit"), "Shift-Ctrl-Enter": () => execute("submit"),
    Tab: (cm) => cm.somethingSelected() ? cm.indentSelection("add") : cm.replaceSelection("    ", "end"),
    "Shift-Tab": (cm) => cm.indentSelection("subtract"),
  };
  if (window.CodeMirror) {
    editor = CodeMirror.fromTextArea(ta, {
      theme: "material-darker", lineNumbers: true, indentUnit: 4, tabSize: 4,
      matchBrackets: true, autoCloseBrackets: true, extraKeys: keys,
    });
    let t;
    editor.on("change", () => { clearTimeout(t); t = setTimeout(saveCode, 400); });
  } else {
    // CDN unavailable (offline): plain textarea fallback
    editor = { getValue: () => ta.value, setValue: (v) => { ta.value = v; } };
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const s = ta.selectionStart;
        ta.value = ta.value.slice(0, s) + "    " + ta.value.slice(ta.selectionEnd);
        ta.selectionStart = ta.selectionEnd = s + 4;
      } else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        execute(e.shiftKey ? "submit" : "sample");
      }
    });
    ta.addEventListener("input", saveCode);
  }
}

async function init() {
  initEditor();
  state.questions = await api("/api/questions");
  state.schema = await api("/api/schema");
  renderSchema();
  renderProgress();

  document.querySelectorAll("#filters button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#filters button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    state.filter = b.dataset.filter;
    renderSidebar();
  }));
  $("#runBtn").addEventListener("click", () => execute("sample"));
  $("#submitBtn").addEventListener("click", () => execute("submit"));
  $("#hintBtn").addEventListener("click", () => {
    const q = state.current;
    state.hints[q.id] = Math.min((state.hints[q.id] || 0) + 1, q.hints.length);
    LS.set("tdp_hints", state.hints);
    renderHints();
  });
  $("#solutionBtn").addEventListener("click", async () => {
    const pre = $("#solution");
    if (!pre.classList.contains("hidden")) { pre.classList.add("hidden"); $("#solutionBtn").textContent = "Show solution"; return; }
    if (!confirm("Reveal the reference solution? Try the hints first.")) return;
    const r = await api("/api/solution", { id: state.current.id });
    pre.textContent = r.solution;
    pre.classList.remove("hidden");
    $("#solutionBtn").textContent = "Hide solution";
  });
  $("#resetCode").addEventListener("click", () => {
    if (!confirm("Reset the editor to the starter code?")) return;
    localStorage.removeItem("tdp_code_" + state.current.id);
    editor.setValue(state.current.starter);
  });
  $("#resetProgress").addEventListener("click", () => {
    if (!confirm("Clear all saved code, hints, and progress?")) return;
    Object.keys(localStorage).filter((k) => k.startsWith("tdp_")).forEach((k) => localStorage.removeItem(k));
    state.status = {}; state.hints = {};
    select(state.current.id);
    renderProgress();
  });
  document.addEventListener("keydown", (e) => {
    if (state.current?.type === "mcq" && e.key === "Enter" && (e.metaKey || e.ctrlKey)) execute("submit");
  });

  setInterval(() => {
    const s = Math.floor((Date.now() - state.timerStart) / 1000);
    $("#timer").textContent = `⏱ ${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  }, 1000);

  const fromHash = location.hash.slice(1);
  select(state.questions.some((q) => q.id === fromHash) ? fromHash : state.questions[0].id);
}

init();
