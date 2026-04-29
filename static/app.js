let currentPage = 1;
const PAGE_SIZE = 20;
let currentHistoryType = 'ssq';
let currentCheckType = 'ssq';
let currentAnalysisType = 'ssq';

// ========== 历史记录 ==========

async function loadHistory(type, btn) {
    currentHistoryType = type;
    currentPage = 1;
    document.querySelectorAll('#panel-history .tab').forEach(t => t.classList.remove('active'));
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

    const totalPages = Math.ceil(data.total / PAGE_SIZE);
    let pgHtml = '';
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        pgHtml += `<button class="${i === page ? 'active' : ''}" onclick="fetchHistory('${type}', ${i})">${i}</button>`;
    }
    if (totalPages > 10) pgHtml += `<span>... 共${totalPages}页</span>`;
    document.getElementById('pagination').innerHTML = pgHtml;
}

// ========== 预测 ==========

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

// ========== 概率表 ==========

async function loadProb(type, btn) {
    document.querySelectorAll('#panel-prob .tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const res = await fetch(`/api/probability/${type}`);
    const data = await res.json();
    const isSSQ = type === 'ssq';
    const mainLabel = isSSQ ? '红区' : '前区';
    const bonusLabel = isSSQ ? '蓝区' : '后区';

    let html = `<table><tr><th>号码</th><th>${mainLabel}</th><th>${bonusLabel}</th></tr>`;
    data.forEach(r => {
        html += `<tr><td>${pad(r.number)}</td><td>${r[isSSQ ? 'red_prob' : 'front_prob'].toFixed(6)}</td><td>${r[isSSQ ? 'blue_prob' : 'back_prob'].toFixed(6)}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('prob-table').innerHTML = html;
}

// ========== 号码分析 ==========

async function runAnalysis() {
    const period = parseInt(document.getElementById('analysis-period').value) || 0;
    const btn = document.getElementById('btn-analysis');
    const status = document.getElementById('analysis-status');

    btn.disabled = true;
    status.innerHTML = '<span class="loading">分析中</span>';

    try {
        const res = await fetch(`/api/analysis/${currentAnalysisType}?period=${period}`);
        const data = await res.json();
        if (data.error) {
            status.textContent = data.error;
            return;
        }
        renderAnalysis(data);
        status.textContent = '分析完成';
    } catch (e) {
        status.textContent = '请求失败';
    } finally {
        btn.disabled = false;
        setTimeout(() => { status.textContent = ''; }, 3000);
    }
}

function switchAnalysisType(type, btn) {
    currentAnalysisType = type;
    document.querySelectorAll('#panel-analysis .tabs .tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    runAnalysis();
}

function renderAnalysis(data) {
    const isSSQ = currentAnalysisType === 'ssq';
    const mainLabel = isSSQ ? '红区' : '前区';
    const bonusLabel = isSSQ ? '蓝区' : '后区';

    document.getElementById('prob-main-label').textContent = mainLabel;
    document.getElementById('prob-bonus-label').textContent = bonusLabel;
    document.getElementById('miss-main-label').textContent = mainLabel;
    document.getElementById('miss-bonus-label').textContent = bonusLabel;

    renderProbabilityRanking(data.probabilities);
    renderMissRanking(data.miss_values);
    renderHeatmap(data.heatmap);
    renderStats(data.stats, mainLabel, bonusLabel);

    document.getElementById('analysis-periods-info').textContent =
        `基于最近 ${data.total_periods} 期数据分析`;
}

function renderProbabilityRanking(probs) {
    ['main', 'bonus'].forEach(zone => {
        const items = probs[zone];
        let html = '<table><tr><th>排名</th><th>号码</th><th>概率</th><th>柱状图</th></tr>';
        const maxProb = items.length ? items[0].prob : 1;
        items.forEach((item, i) => {
            const barWidth = (item.prob / maxProb * 100).toFixed(1);
            html += `<tr><td>${i + 1}</td><td><strong>${pad(item.number)}</strong></td><td>${item.prob.toFixed(6)}</td>`;
            html += `<td><div class="prob-bar" style="width:${barWidth}%"></div></td></tr>`;
        });
        html += '</table>';
        document.getElementById(`prob-ranking-${zone}`).innerHTML = html;
    });
}

function renderMissRanking(misses) {
    ['main', 'bonus'].forEach(zone => {
        const items = misses[zone];
        let html = '<table><tr><th>排名</th><th>号码</th><th>遗漏期数</th><th>柱状图</th></tr>';
        const maxMiss = items.length ? items[0].miss : 1;
        items.forEach((item, i) => {
            const barWidth = (item.miss / maxMiss * 100).toFixed(1);
            const cls = item.miss > maxMiss * 0.6 ? 'miss-bar hot' : item.miss > maxMiss * 0.3 ? 'miss-bar warm' : 'miss-bar cold';
            html += `<tr><td>${i + 1}</td><td><strong>${pad(item.number)}</strong></td><td>${item.miss}</td>`;
            html += `<td><div class="${cls}" style="width:${barWidth}%"></div></td></tr>`;
        });
        html += '</table>';
        document.getElementById(`miss-ranking-${zone}`).innerHTML = html;
    });
}

function renderHeatmap(heatmap) {
    ['main', 'bonus'].forEach(zone => {
        const data = heatmap[zone];
        const nums = Object.keys(data).map(Number).sort((a, b) => a - b);
        let html = '';
        nums.forEach(num => {
            const cls = data[num];
            html += `<span class="heatmap-cell ${cls}" title="${pad(num)}: ${cls === 'hot' ? '热号' : cls === 'cold' ? '冷号' : '温号'}">${pad(num)}</span>`;
        });
        document.getElementById(`heatmap-${zone}`).innerHTML = html;
    });
}

function renderStats(stats, mainLabel, bonusLabel) {
    const oe = stats.odd_even;
    const sr = stats.sum_range;
    const hc = stats.hot_cold;
    const dist = stats.distribution;

    let html = '';

    // 奇偶比
    html += '<div class="stat-card">';
    html += '<div class="stat-title">奇偶比</div>';
    html += `<div class="stat-body">`;
    html += `<div>${mainLabel}：历史均值 ${oe.main.history_avg} / 近30期 ${oe.main.recent_avg}</div>`;
    html += `<div>${bonusLabel}：历史均值 ${oe.bonus.history_avg} / 近30期 ${oe.bonus.recent_avg}</div>`;
    html += '</div></div>';

    // 求和值
    html += '<div class="stat-card">';
    html += '<div class="stat-title">求和值范围</div>';
    html += '<div class="stat-body">';
    html += `<div>${mainLabel}：${sr.main.min} ~ ${sr.main.max}（历史均值 ${sr.main.avg}，近30期 ${sr.main.recent_avg}）</div>`;
    html += `<div>${bonusLabel}：${sr.bonus.min} ~ ${sr.bonus.max}（历史均值 ${sr.bonus.avg}，近30期 ${sr.bonus.recent_avg}）</div>`;
    html += '</div></div>';

    // 冷热号
    html += '<div class="stat-card">';
    html += '<div class="stat-title">冷热号分类</div>';
    html += '<div class="stat-body">';
    html += `<div>${mainLabel}：<span class="tag-hot">热号</span> ${hc.main.hot.map(pad).join(' ')}　<span class="tag-warm">温号</span> ${hc.main.warm.map(pad).join(' ')}　<span class="tag-cold">冷号</span> ${hc.main.cold.map(pad).join(' ')}</div>`;
    html += `<div>${bonusLabel}：<span class="tag-hot">热号</span> ${hc.bonus.hot.map(pad).join(' ')}　<span class="tag-warm">温号</span> ${hc.bonus.warm.map(pad).join(' ')}　<span class="tag-cold">冷号</span> ${hc.bonus.cold.map(pad).join(' ')}</div>`;
    html += '</div></div>';

    // 分区分布
    html += '<div class="stat-card">';
    html += '<div class="stat-title">号码分区分布</div>';
    html += '<div class="stat-body">';
    html += `<div>${mainLabel}：低区 ${(dist.main.low * 100).toFixed(1)}% / 中区 ${(dist.main.mid * 100).toFixed(1)}% / 高区 ${(dist.main.high * 100).toFixed(1)}%</div>`;
    html += `<div>${bonusLabel}：低区 ${(dist.bonus.low * 100).toFixed(1)}% / 中区 ${(dist.bonus.mid * 100).toFixed(1)}% / 高区 ${(dist.bonus.high * 100).toFixed(1)}%</div>`;
    html += '</div></div>';

    document.getElementById('stats-panel').innerHTML = html;
}

// ========== 号码查询 ==========

function setCheckType(type, btn) {
    currentCheckType = type;
    document.querySelectorAll('#panel-check .tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const isSSQ = type === 'ssq';
    document.getElementById('label-main').textContent = isSSQ ? '红球号码（6个）：' : '前区号码（5个）：';
    document.getElementById('label-bonus').textContent = isSSQ ? '蓝球号码（1个）：' : '后区号码（2个）：';
    document.getElementById('check-main').placeholder = isSSQ ? '例如: 01 05 12 23 30 33' : '例如: 01 05 12 23 30';
    document.getElementById('check-bonus').placeholder = isSSQ ? '例如: 07' : '例如: 03 07';

    document.getElementById('check-result').innerHTML = '';
    loadPrizeTable(type);
}

function parseCheckNumbers() {
    const mainStr = document.getElementById('check-main').value.trim();
    const bonusStr = document.getElementById('check-bonus').value.trim();

    if (!mainStr || !bonusStr) return null;

    const main = mainStr.split(/[\s,，]+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    const bonus = bonusStr.split(/[\s,，]+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));

    if (main.length === 0 || bonus.length === 0) return null;

    return { main, bonus };
}

async function checkHistory() {
    const nums = parseCheckNumbers();
    if (!nums) {
        document.getElementById('check-result').innerHTML = '<div class="check-result-box error">请输入有效号码</div>';
        return;
    }

    const isSSQ = currentCheckType === 'ssq';
    if ((isSSQ && nums.main.length !== 6) || (!isSSQ && nums.main.length !== 5) ||
        (isSSQ && nums.bonus.length !== 1) || (!isSSQ && nums.bonus.length !== 2)) {
        const mainNeed = isSSQ ? 6 : 5;
        const bonusNeed = isSSQ ? 1 : 2;
        document.getElementById('check-result').innerHTML = `<div class="check-result-box error">请输入${mainNeed}个${isSSQ ? '红球' : '前区'}号码和${bonusNeed}个${isSSQ ? '蓝球' : '后区'}号码</div>`;
        return;
    }

    const res = await fetch('/api/check/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: currentCheckType, main: nums.main, bonus: nums.bonus }),
    });
    const data = await res.json();

    if (data.found) {
        const mainKey = isSSQ ? 'red' : 'front';
        const bonusKey = isSSQ ? 'blue' : 'back';
        let html = `<div class="check-result-box success">`;
        html += `<strong>命中！</strong>这组号码在历史中出现过 ${data.count} 次：<br>`;
        data.matches.forEach(m => {
            const mainNums = Array.isArray(m[mainKey]) ? m[mainKey].map(pad).join(' ') : m[mainKey];
            const bonusNums = Array.isArray(m[bonusKey]) ? m[bonusKey].map(pad).join(' ') : pad(m[bonusKey]);
            html += `第 <strong>${m.issue}</strong> 期：`;
            html += `<span class="red">${mainNums}</span> + <span class="blue">${bonusNums}</span><br>`;
        });
        html += '</div>';
        document.getElementById('check-result').innerHTML = html;
    } else {
        document.getElementById('check-result').innerHTML = '<div class="check-result-box info">该组合未在历史开奖记录中出现</div>';
    }
}

async function checkPrize() {
    const nums = parseCheckNumbers();
    if (!nums) {
        document.getElementById('check-result').innerHTML = '<div class="check-result-box error">请输入有效号码</div>';
        return;
    }

    const res = await fetch('/api/check/prize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: currentCheckType, main: nums.main, bonus: nums.bonus }),
    });
    const data = await res.json();

    if (data.error) {
        document.getElementById('check-result').innerHTML = `<div class="check-result-box error">${data.error}</div>`;
        return;
    }

    const isSSQ = currentCheckType === 'ssq';
    const mainLabel = isSSQ ? '红球' : '前区';
    const bonusLabel = isSSQ ? '蓝球' : '后区';

    let html = '<div class="check-result-box info">';
    html += `<strong>对比最近一期开奖（第 ${data.latest.issue} 期）</strong><br><br>`;
    html += `开奖号码：`;
    if (isSSQ) {
        html += `<span class="red">${data.latest.red.map(pad).join(' ')}</span> + <span class="blue">${pad(data.latest.blue)}</span><br>`;
    } else {
        html += `<span class="red">${data.latest.front.map(pad).join(' ')}</span> + <span class="blue">${data.latest.back.map(pad).join(' ')}</span><br>`;
    }
    html += `你的号码：`;
    if (isSSQ) {
        html += `<span class="red">${data.user_main.map(pad).join(' ')}</span> + <span class="blue">${pad(data.user_blue)}</span><br>`;
    } else {
        html += `<span class="red">${data.user_front.map(pad).join(' ')}</span> + <span class="blue">${data.user_back.map(pad).join(' ')}</span><br>`;
    }
    html += `<br>`;
    html += `${mainLabel}命中：<strong class="match">${data.main_match}</strong> 个　`;
    html += `${bonusLabel}命中：<strong class="match">${data.bonus_match}</strong> 个<br><br>`;

    if (data.prize) {
        html += `<strong style="font-size:16px;">${data.prize.level}</strong>（${data.prize.prize}）`;
    } else {
        html += `<span class="no-match">未中奖</span>`;
    }
    html += '</div>';
    document.getElementById('check-result').innerHTML = html;
}

async function loadPrizeTable(type) {
    const res = await fetch(`/api/prize-table/${type}`);
    const data = await res.json();
    const mainLabel = data[0]?.main_label || '前区';
    const bonusLabel = data[0]?.bonus_label || '后区';

    let html = '<table><tr><th>奖级</th><th>' + mainLabel + '命中</th><th>' + bonusLabel + '命中</th><th>奖金</th></tr>';
    data.forEach(r => {
        html += `<tr><td><strong>${r.level}</strong></td><td>${r.main}</td><td>${r.bonus}</td><td>${r.prize}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('prize-table').innerHTML = html;
}

// ========== 工具 ==========

function pad(n) {
    return String(n).padStart(2, '0');
}

// ========== 初始化 ==========

window.addEventListener('DOMContentLoaded', () => {
    loadHistory('ssq');
    runAnalysis('ssq');
    loadProb('ssq');
    setCheckType('ssq');
});
