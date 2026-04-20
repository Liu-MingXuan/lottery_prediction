let currentPage = 1;
const PAGE_SIZE = 20;
let currentHistoryType = 'ssq';

// 历史记录
async function loadHistory(type, btn) {
    currentHistoryType = type;
    currentPage = 1;
    document.querySelectorAll('.panel:nth-child(3) .tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    await fetchHistory(type, 1);
}

async function fetchHistory(type, page) {
    currentPage = page;
    const res = await fetch(`/api/history/${type}?page=${page}&size=${PAGE_SIZE}`);
    const data = await res.json();

    const isSSQ = type === 'ssq';
    let html = '<table><tr><th>期号</th><th>日期</th>';
    if (isSSQ) {
        html += '<th>红球</th><th>蓝球</th>';
    } else {
        html += '<th>前区</th><th>后区</th>';
    }
    html += '</tr>';

    for (const r of data.records) {
        html += `<tr><td>${r.issue}</td><td>${r.draw_date}</td>`;
        if (isSSQ) {
            const reds = [r.red1, r.red2, r.red3, r.red4, r.red5, r.red6].map(n => pad(n));
            html += `<td class="num-red">${reds.join(' ')}</td>`;
            html += `<td class="num-blue">${pad(r.blue)}</td>`;
        } else {
            const fronts = [r.front1, r.front2, r.front3, r.front4, r.front5].map(n => pad(n));
            const backs = [r.back1, r.back2].map(n => pad(n));
            html += `<td class="num-red">${fronts.join(' ')}</td>`;
            html += `<td class="num-blue">${backs.join(' ')}</td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    document.getElementById('history-table').innerHTML = html;

    // 分页
    const totalPages = Math.ceil(data.total / PAGE_SIZE);
    let pgHtml = '';
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        pgHtml += `<button class="${i === page ? 'active' : ''}" onclick="fetchHistory('${type}', ${i})">${i}</button>`;
    }
    if (totalPages > 10) pgHtml += `<span>... 共${totalPages}页</span>`;
    document.getElementById('pagination').innerHTML = pgHtml;
}

// 预测
async function runPredict() {
    const period = parseInt(document.getElementById('period').value) || 0;
    const count = parseInt(document.getElementById('count').value) || 5;
    const btn = document.getElementById('btn-predict');
    const status = document.getElementById('status');

    btn.disabled = true;
    status.innerHTML = '<span class="loading">预测中</span>';

    try {
        const res = await fetch(`/api/predict?period=${period}&count=${count}`);
        const data = await res.json();
        renderPredictions(data);
        loadProb('ssq');
        status.textContent = '预测完成';
    } catch (e) {
        status.textContent = '请求失败';
    } finally {
        btn.disabled = false;
        setTimeout(() => { status.textContent = ''; }, 3000);
    }
}

function renderPredictions(data) {
    let html = '';

    ['双色球', '大乐透'].forEach(type => {
        const results = data[type];
        if (!results || results.length === 0) return;

        const isSSQ = type === '双色球';
        html += `<div class="prediction-section"><h3>${type}</h3>`;

        results.forEach((r, i) => {
            html += `<div class="combo-card">`;
            html += `<div class="label">第${i + 1}组</div>`;
            html += `<div class="balls">`;

            if (isSSQ) {
                r['红区'].forEach(n => { html += `<span class="red">${n}</span> `; });
                html += `<span class="blue">+ ${r['蓝区'][0]}</span>`;
            } else {
                r['前区'].forEach(n => { html += `<span class="red">${n}</span> `; });
                html += `<span class="blue">+ ${r['后区'].join(' ')}</span>`;
            }
            html += `</div>`;
            html += `<div class="prob">综合概率: ${r['综合概率'].toExponential(2)}</div>`;
            html += `</div>`;
        });

        html += '</div>';
    });

    document.getElementById('predict-result').innerHTML = html;
}

// 概率表
async function loadProb(type, btn) {
    document.querySelectorAll('.panel:nth-child(5) .tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const res = await fetch(`/api/probability/${type}`);
    const data = await res.json();
    const isSSQ = type === 'ssq';
    const mainLabel = isSSQ ? '红区' : '前区';
    const bonusLabel = isSSQ ? '蓝区' : '后区';

    let html = `<table><tr><th>号码</th><th>${mainLabel}</th><th>${bonusLabel}</th></tr>`;
    data.forEach(r => {
        const numStr = pad(r.number);
        html += `<tr><td>${numStr}</td><td>${r[isSSQ ? 'red_prob' : 'front_prob'].toFixed(6)}</td><td>${r[isSSQ ? 'blue_prob' : 'back_prob'].toFixed(6)}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('prob-table').innerHTML = html;
}

// 工具
function pad(n) {
    return String(n).padStart(2, '0');
}

// 初始化
window.addEventListener('DOMContentLoaded', () => {
    loadHistory('ssq');
    loadProb('ssq');
});
