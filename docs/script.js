/**
 * 加载汇总 JSON 并填充表格。GitHub Pages 同域 fetch 可用；
 * 本地请用：python -m http.server（勿依赖 file://）。
 */

(function () {
  var DATA_URL = "assets/data/summary_v0_2_deepseek.json";

  /** 规则检查项英文名 -> 页面展示中文 */
  var CHECK_LABELS = {
    expected_output_type: "输出类型是否符合题目要求",
    must_include: "必备关键词是否都出现",
    must_not_do: "是否出现禁用用语",
    json_parseable: "若要求 JSON，是否能解析",
  };

  /** 代理指标 key -> 中文 + 一句人话 */
  var QP_LABELS = {
    required_item_coverage: "必备词覆盖度（均值）：有没有把题目要求的词写进输出里",
    forbidden_violation_count_avg: "禁用词命中次数（均值）：出现一次算一次",
    constraint_hit_rate: "约束句粗匹配（很粗，仅供参考）：实现朴素，别当真理",
    output_nonempty_rate: "输出是否非空（比例）",
    json_valid_rate: "JSON 语法是否有效（比例，仅相关题）",
    citation_presence_avg: "引用样式信号（仅部分需要引用的题）",
  };

  function el(id) {
    return document.getElementById(id);
  }

  function showError(msg) {
    var b = el("error-banner");
    if (b) {
      b.textContent = msg;
      b.classList.add("visible");
    }
    var s = el("load-status");
    if (s) s.textContent = "数据未加载（见上方提示）";
  }

  function fmtNum(n) {
    if (typeof n !== "number" || n !== n) return "—";
    return String(n);
  }

  function renderOverview(data) {
    var tbody = el("tbody-overview");
    if (!tbody) return;
    tbody.innerHTML = "";
    var rows = [
      ["题目总数", data.total_tasks],
      ["规则通过题数", data.passed],
      ["规则未通过题数", data.failed],
      ["平均规则分", data.avg_rule_score],
      ["执行成功 trace 数（程序跑完无报错）", data.success_traces],
      ["执行报错 trace 数", data.failed_traces],
    ];
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + row[0] + "</td><td>" + fmtNum(row[1]) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderMapTable(tbodyId, obj) {
    var tbody = el(tbodyId);
    if (!tbody || !obj) return;
    tbody.innerHTML = "";
    Object.keys(obj)
      .sort()
      .forEach(function (key) {
        var v = obj[key];
        var tr = document.createElement("tr");
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

  var QP_ORDER = [
    "required_item_coverage",
    "forbidden_violation_count_avg",
    "constraint_hit_rate",
    "output_nonempty_rate",
    "json_valid_rate",
    "citation_presence_avg",
  ];

  function renderQP(data) {
    var tbody = el("tbody-qp");
    if (!tbody) return;
    var qp = data.quality_proxy_averages || {};
    tbody.innerHTML = "";
    QP_ORDER.forEach(function (key) {
      if (!(key in qp)) return;
      var label = QP_LABELS[key] || key;
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + label + "</td><td>" + fmtNum(qp[key]) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderChecks(data) {
    var tbody = el("tbody-checks");
    if (!tbody) return;
    var co = data.checks_overview || {};
    tbody.innerHTML = "";
    Object.keys(co).forEach(function (name) {
      var v = co[name];
      var label = CHECK_LABELS[name] || name;
      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        label +
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
      var status = el("load-status");
      if (status) {
        status.textContent =
          "已加载数据" +
          (data.experiment_note ? "（" + data.experiment_note + "）" : "") +
          "。";
      }
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
          "。请在本目录执行：python -m http.server 8000，再用浏览器打开 http://localhost:8000/（直接双击打开 HTML 可能无法读取数据）。"
      );
    });
})();
