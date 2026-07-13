const suiteNames = {
  psychometric_probe: 'A 构念探针',
  creative_problem_solving: 'B 问题解决',
  creative_artifact: 'C 创造产品',
  loop_adaptation_recovery: 'D 适应恢复',
};

const dataFiles = [
  ['data/a1.json.gz', 'gzip'],
  ['data/a2.json.gz', 'gzip'],
  ['data/a3.json.gz', 'gzip'],
  ['data/b1.json.gz', 'gzip'],
  ['data/b04.json', 'json'],
  ['data/b05.json', 'json'],
  ['data/b06.json', 'json'],
  ['data/b3.json.gz', 'gzip'],
  ['data/c1.json.gz', 'gzip'],
  ['data/c2.json.gz', 'gzip'],
  ['data/c3.json.gz', 'gzip'],
  ['data/d01.json', 'json'],
  ['data/d02.json', 'json'],
  ['data/d03.json', 'json'],
  ['data/d2.json.gz', 'gzip'],
  ['data/d3.json.gz', 'gzip'],
];

let allCases = [];
const grid = document.querySelector('#case-grid');
const dialog = document.querySelector('#case-dialog');
const content = document.querySelector('#dialog-content');

Promise.all(dataFiles.map(async ([path, format]) => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`无法读取 ${path}`);
  if (format === 'gzip') {
    const stream = response.body.pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }
  return response.json();
}))
  .then((payloads) => {
    allCases = payloads.flatMap((payload) => payload.cases);
    allCases.sort((a, b) => a.case_id.localeCompare(b.case_id));
    render('all');
  })
  .catch((error) => {
    console.error(error);
    grid.innerHTML = '<p>Case 数据加载失败。请通过 GitHub Pages 或本地 HTTP 服务打开页面。</p>';
  });

document.querySelectorAll('[data-suite]').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('[data-suite]').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
  render(button.dataset.suite);
}));

document.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => {
  if (event.target === dialog) dialog.close();
});

function escapeHtml(value) {
  return String(value).replace(/[&<>]/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
  }[character]));
}

function render(filter) {
  const cases = filter === 'all' ? allCases : allCases.filter((item) => item.suite === filter);
  grid.innerHTML = cases.map((item) => `
    <article class="case-card" data-id="${item.case_id}" tabindex="0">
      <div class="case-top">
        <span class="case-id">${item.case_id}</span>
        <span class="suite-tag">${suiteNames[item.suite]}</span>
      </div>
      <h3>${item.title}</h3>
      <p>${escapeHtml(item.prompt.slice(0, 86).replace(/\n/g, ' '))}…</p>
      <div class="chips">${item.construct_targets.slice(0, 3).map((target) => `<span class="chip">${target}</span>`).join('')}</div>
    </article>
  `).join('');

  document.querySelectorAll('.case-card').forEach((card) => {
    card.addEventListener('click', () => openCase(card.dataset.id));
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') openCase(card.dataset.id);
    });
  });
}

function displayValue(value) {
  return escapeHtml(typeof value === 'string' ? value : JSON.stringify(value, null, 2));
}

function openCase(id) {
  const item = allCases.find((candidate) => candidate.case_id === id);
  content.innerHTML = `
    <div class="dialog-body">
      <p class="eyebrow">${suiteNames[item.suite]} · ${item.status}</p>
      <h2>${item.case_id} ${item.title}</h2>
      <div class="chips">${item.construct_targets.map((target) => `<span class="chip">${target}</span>`).join('')}</div>

      <h3>题面</h3>
      <div class="prompt">${escapeHtml(item.prompt)}</div>

      <h3>工具环境</h3>
      <ul>${item.tool_environment.tools.map((tool) => `<li><b>${tool.name}</b>：${tool.description}</li>`).join('')}</ul>

      <h3>Gold</h3>
      <p><b>必须满足</b></p>
      <ul>${item.gold.required_elements.map((element) => `<li>${escapeHtml(element)}</li>`).join('')}</ul>
      <p><b>可接受策略</b></p>
      <ul>${item.gold.accepted_strategies.map((strategy) => `<li>${displayValue(strategy)}</li>`).join('')}</ul>
      <p><b>明确失败</b></p>
      <ul>${item.gold.prohibited_failures.map((failure) => `<li>${escapeHtml(failure)}</li>`).join('')}</ul>
      <p><b>说明性示例</b></p>
      <pre class="example-block">${displayValue(item.gold.exemplar)}</pre>

      <h3>Rubric 锚点</h3>
      <div class="table-wrap">
        <table class="rubric-table">
          <thead><tr><th>维度</th><th>判定标准</th><th>0 / 1 / 2 分锚点</th></tr></thead>
          <tbody>${item.rubric.map((criterion) => `
            <tr>
              <td>${criterion.dimension}</td>
              <td>${criterion.description}</td>
              <td>0：${criterion.anchors['0']}<br>1：${criterion.anchors['1']}<br>2：${criterion.anchors['2']}</td>
            </tr>
          `).join('')}</tbody>
        </table>
      </div>

      <h3>边界样例</h3>
      ${item.boundary_examples.map((example) => `
        <div class="boundary ${example.label}">
          <b>${example.label}</b>
          <pre>${displayValue(example.output)}</pre>
          <small>${example.rationale}</small>
        </div>
      `).join('')}
    </div>
  `;
  dialog.showModal();
}
