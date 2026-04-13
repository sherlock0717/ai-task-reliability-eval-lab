(function () {
  var SUMMARY_URL = "assets/data/summary_v0_2_deepseek.json";
  var TASKS_URL = "assets/data/tasks_v1.json";

  var typeLabels = {
    extraction: "信息抽取",
    rewrite: "改写",
    qa: "问答",
  };

  var difficultyLabels = {
    easy: "易",
    medium: "中",
    hard: "难",
  };

  var checkLabels = {
    expected_output_type: "输出类型符合要求",
    must_include: "必备内容出现",
    must_not_do: "未触发禁用表达",
    json_parseable: "JSON 可解析",
  };

  var proxyLabels = {
    required_item_coverage: "必备内容覆盖",
    forbidden_violation_count_avg: "禁用表达命中均值",
    constraint_hit_rate: "约束句粗匹配",
    output_nonempty_rate: "非空输出比例",
    json_valid_rate: "JSON 有效比例",
    citation_presence_avg: "引用信号均值",
  };

  var proxyOrder = [
    "required_item_coverage",
    "forbidden_violation_count_avg",
    "constraint_hit_rate",
    "output_nonempty_rate",
    "json_valid_rate",
    "citation_presence_avg",
  ];

  var state = {
    tasks: [],
    filter: "all",
  };

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function setText(selector, text) {
    var node = $(selector);
    if (node) node.textContent = text;
  }

  function formatValue(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return String(value || "-");
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderSummary(data) {
    var total = data.total_tasks || 12;
    var passed = data.passed || 0;
    var traces = data.success_traces || 0;

    setText("#hero-total", total);
    setText("#hero-pass", passed + " / " + total);
    setText("#hero-traces", traces + " 条");
    setText("#sum-pass", passed + " / " + total);

    var checksBody = $("#tbody-checks");
    if (checksBody) {
      checksBody.innerHTML = Object.keys(data.checks_overview || {})
        .map(function (key) {
          var item = data.checks_overview[key];
          return (
            "<tr><td>" +
            escapeHtml(checkLabels[key] || key) +
            "</td><td>" +
            escapeHtml(item.pass) +
            "</td><td>" +
            escapeHtml(item.fail) +
            "</td></tr>"
          );
        })
        .join("");
    }

    var proxyBody = $("#tbody-proxy");
    if (proxyBody) {
      var proxy = data.quality_proxy_averages || {};
      proxyBody.innerHTML = proxyOrder
        .filter(function (key) {
          return Object.prototype.hasOwnProperty.call(proxy, key);
        })
        .map(function (key) {
          return (
            "<tr><td>" +
            escapeHtml(proxyLabels[key] || key) +
            "</td><td>" +
            escapeHtml(formatValue(proxy[key])) +
            "</td></tr>"
          );
        })
        .join("");
    }

    setText("#load-status", "已加载 v0.2 direct 跑批汇总。");
  }

  function showError(message) {
    var banner = $("#error-banner");
    if (banner) {
      banner.textContent = message;
      banner.classList.add("is-visible");
    }
    setText("#load-status", "数据未加载。");
  }

  function loadSummary() {
    fetch(SUMMARY_URL)
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(renderSummary)
      .catch(function () {
        showError("无法加载结果汇总。请在 site/showcase 目录运行 python -m http.server 8000 后访问本页。");
      });
  }

  function taskCard(task, index) {
    return (
      '<button class="task-card" type="button" data-task-id="' +
      escapeHtml(task.task_id) +
      '" style="animation-delay:' +
      index * 35 +
      'ms">' +
      '<div class="task-card__meta"><span>' +
      escapeHtml(task.short_id) +
      "</span><span>" +
      escapeHtml(typeLabels[task.task_type] || task.task_type) +
      " · " +
      escapeHtml(difficultyLabels[task.difficulty] || task.difficulty) +
      "</span></div><h3>" +
      escapeHtml(task.title) +
      "</h3><p>" +
      escapeHtml(task.scenario) +
      "</p></button>"
    );
  }

  function renderTasks() {
    var wall = $("#task-wall");
    if (!wall) return;
    var filtered = state.tasks.filter(function (task) {
      return state.filter === "all" || task.task_type === state.filter;
    });
    wall.innerHTML = filtered.map(taskCard).join("");
    $all(".task-card", wall).forEach(function (button) {
      button.addEventListener("click", function () {
        openTask(button.getAttribute("data-task-id"));
      });
    });
  }

  function loadTasks() {
    fetch(TASKS_URL)
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (tasks) {
        state.tasks = tasks;
        renderTasks();
      })
      .catch(function () {
        var wall = $("#task-wall");
        if (wall) wall.innerHTML = '<p class="error-banner is-visible">无法加载题目数据。</p>';
      });
  }

  function openTask(taskId) {
    var task = state.tasks.find(function (item) {
      return item.task_id === taskId;
    });
    var drawer = $("#task-drawer");
    if (!task || !drawer) return;

    setText("#drawer-type", typeLabels[task.task_type] || task.task_type);
    setText("#drawer-title", task.short_id + " · " + task.title);
    setText("#drawer-scenario", task.scenario_title);
    setText("#drawer-input", task.input_summary);
    setText("#drawer-output", task.expected_output);

    var meta = $("#drawer-meta");
    if (meta) {
      meta.innerHTML = [
        task.task_id,
        typeLabels[task.task_type] || task.task_type,
        difficultyLabels[task.difficulty] || task.difficulty,
        task.domain,
      ]
        .map(function (item) {
          return '<span class="pill">' + escapeHtml(item) + "</span>";
        })
        .join("");
    }

    var constraints = $("#drawer-constraints");
    if (constraints) {
      constraints.innerHTML = task.constraints
        .map(function (item) {
          return "<li>" + escapeHtml(item) + "</li>";
        })
        .join("");
    }

    var fullWrap = $("#drawer-full-wrap");
    var full = $("#drawer-full");
    if (fullWrap && full) {
      if (task.full_example) {
        full.textContent = task.full_example;
        fullWrap.classList.add("is-visible");
      } else {
        full.textContent = "";
        fullWrap.classList.remove("is-visible");
      }
    }

    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("drawer-open");
  }

  function closeDrawer() {
    var drawer = $("#task-drawer");
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("drawer-open");
  }

  function initFilters() {
    $all(".filter").forEach(function (button) {
      button.addEventListener("click", function () {
        state.filter = button.getAttribute("data-filter") || "all";
        $all(".filter").forEach(function (item) {
          item.classList.toggle("is-active", item === button);
        });
        renderTasks();
      });
    });
  }

  function initNav() {
    var nav = $(".nav");
    var sections = $all("main section, header.hero");
    function onScroll() {
      if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 12);
      var current = sections
        .filter(function (section) {
          return section.offsetTop <= window.scrollY + 120;
        })
        .pop();
      if (!current) return;
      $all(".nav__links a").forEach(function (link) {
        link.classList.toggle("is-active", link.getAttribute("href") === "#" + current.id);
      });
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initReveal() {
    var nodes = $all("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (node) {
        node.classList.add("is-visible");
      });
      return;
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    nodes.forEach(function (node) {
      observer.observe(node);
    });
  }

  function initDrawer() {
    $all("[data-close-drawer]").forEach(function (node) {
      node.addEventListener("click", closeDrawer);
    });
    var openButton = $("#open-tasks");
    if (openButton) {
      openButton.addEventListener("click", function () {
        var first = state.tasks.find(function (task) {
          return state.filter === "all" || task.task_type === state.filter;
        });
        if (first) openTask(first.task_id);
      });
    }
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeDrawer();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initReveal();
    initNav();
    initFilters();
    initDrawer();
    loadSummary();
    loadTasks();
  });
})();
