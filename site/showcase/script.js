/**
 * Gate、数据加载、滚动显现。本地预览请：python -m http.server
 */
(function () {
  var DATA_URL = "assets/data/summary_v0_2_deepseek.json";

  var CHECK_LABELS = {
    expected_output_type: "输出类型是否符合题目要求",
    must_include: "必备关键词是否都出现",
    must_not_do: "是否出现禁用用语",
    json_parseable: "若要求 JSON，是否能解析",
  };

  var QP_LABELS = {
    required_item_coverage: "必备词覆盖度（均值）——题目要求的词是否写进输出",
    forbidden_violation_count_avg: "禁用词命中次数（均值）",
    constraint_hit_rate: "约束句粗匹配（实现很粗，仅供参考）",
    output_nonempty_rate: "输出非空比例",
    json_valid_rate: "JSON 语法有效比例（相关题）",
    citation_presence_avg: "引用样式信号（仅部分题）",
  };

  var QP_ORDER = [
    "required_item_coverage",
    "forbidden_violation_count_avg",
    "constraint_hit_rate",
    "output_nonempty_rate",
    "json_valid_rate",
    "citation_presence_avg",
  ];

  function el(id) {
    return document.getElementById(id);
  }

  function fmtNum(n) {
    if (typeof n !== "number" || n !== n) return "—";
    return String(n);
  }

  function showError(msg) {
    var b = el("error-banner");
    if (b) {
      b.textContent = msg;
      b.classList.add("visible");
    }
    var s = el("load-status");
    if (s) s.textContent = "数据未加载";
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
      ["执行成功 trace 数（程序跑完）", data.success_traces],
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

  function loadSummary() {
    fetch(DATA_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        var status = el("load-status");
        if (status) status.textContent = "数据已载入。";
        renderOverview(data);
        renderMapTable("tbody-by-type", data.by_task_type);
        renderMapTable("tbody-by-diff", data.by_difficulty);
        renderQP(data);
        renderChecks(data);
      })
      .catch(function () {
        showError(
          "无法加载数据文件。请在项目目录执行：python -m http.server 8000，再访问 http://localhost:8000/"
        );
      });
  }

  function initGate() {
    var gate = el("gate");
    var app = el("app");
    var btn = el("gate-enter");
    if (!gate || !app || !btn) return;

    var entered = false;
    function enter() {
      if (entered) return;
      entered = true;
      gate.classList.add("gate--out");
      document.body.classList.remove("gate-active");
      app.classList.add("app--visible");
      app.setAttribute("aria-hidden", "false");
      gate.setAttribute("aria-hidden", "true");
      gate.setAttribute("inert", "");

      window.setTimeout(function () {
        gate.style.display = "none";
      }, 700);

      btn.blur();
    }

    btn.addEventListener("click", enter);
  }

  function initReveal() {
    var sections = document.querySelectorAll("[data-reveal]");
    if (!sections.length || !("IntersectionObserver" in window)) {
      sections.forEach(function (s) {
        s.classList.add("section--visible");
      });
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("section--visible");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
    );
    sections.forEach(function (s) {
      io.observe(s);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initGate();
    initReveal();
    loadSummary();
  });
})();
