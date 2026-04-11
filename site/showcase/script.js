/**
 * Load experiment summary JSON and populate tables.
 * GitHub Pages: same-origin fetch works.
 * file:// preview: use a local static server (see README).
 */

(function () {
  const DATA_URL = "assets/data/summary_v0_2_deepseek.json";

  function el(id) {
    return document.getElementById(id);
  }

  function showError(msg) {
    const b = el("error-banner");
    if (b) {
      b.textContent = msg;
      b.classList.add("visible");
    }
    const s = el("load-status");
    if (s) s.textContent = "数据未加载（见上方提示）";
  }

  function fmtNum(n) {
    if (typeof n !== "number" || Number.isNaN(n)) return "—";
    return Number.isInteger(n) ? String(n) : String(n);
  }

  function renderOverview(data) {
    const tbody = el("tbody-overview");
    if (!tbody) return;
    tbody.innerHTML = "";
    const rows = [
      ["任务总数", data.total_tasks],
      ["规则通过任务数", data.passed],
      ["规则未通过任务数", data.failed],
      ["平均规则分（avg_rule_score）", data.avg_rule_score],
      ["执行成功 trace 数", data.success_traces],
      ["执行报错 trace 数", data.failed_traces],
    ];
    rows.forEach(([k, v]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + k + "</td><td>" + fmtNum(v) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderMapTable(tbodyId, obj) {
    const tbody = el(tbodyId);
    if (!tbody || !obj) return;
    tbody.innerHTML = "";
    Object.keys(obj).sort().forEach((key) => {
      const v = obj[key];
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        key +
        "</td><td>" +
        v.total +
        "</td><td>" +
        v.passed +
        "</td><td>" +
        v.failed +
        "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderQP(data) {
    const tbody = el("tbody-qp");
    if (!tbody) return;
    const qp = data.quality_proxy_averages || {};
    tbody.innerHTML = "";
    const entries = [
      ["required_item_coverage（must_include 覆盖度均值）", qp.required_item_coverage],
      ["forbidden_violation_count_avg", qp.forbidden_violation_count_avg],
      ["constraint_hit_rate（约束文本粗匹配，启发式）", qp.constraint_hit_rate],
      ["output_nonempty_rate", qp.output_nonempty_rate],
      ["json_valid_rate", qp.json_valid_rate],
      ["citation_presence_avg（仅引用敏感任务聚合）", qp.citation_presence_avg],
    ];
    entries.forEach(([k, v]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + k + "</td><td>" + fmtNum(v) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderChecks(data) {
    const tbody = el("tbody-checks");
    if (!tbody) return;
    const co = data.checks_overview || {};
    tbody.innerHTML = "";
    Object.keys(co).forEach((name) => {
      const v = co[name];
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        name +
        "</td><td>" +
        v.pass +
        "</td><td>" +
        v.fail +
        "</td>";
      tbody.appendChild(tr);
    });
  }

  fetch(DATA_URL)
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (data) {
      el("load-status").textContent =
        "已加载：" + (data.experiment_note || "summary_v0_2_deepseek.json");
      renderOverview(data);
      renderMapTable("tbody-by-type", data.by_task_type);
      renderMapTable("tbody-by-diff", data.by_difficulty);
      renderQP(data);
      renderChecks(data);
    })
    .catch(function () {
      showError(
        "无法加载 " +
          DATA_URL +
          "。若你是直接双击打开 HTML，请在本目录运行：python -m http.server 8000，然后访问 http://localhost:8000/"
      );
    });
})();
