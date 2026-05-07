// Initialize Chart.js configuration for dark theme
Chart.defaults.color = '#8b9bb4';
Chart.defaults.font.family = 'JetBrains Mono';

// 1. Equity Curve Chart
const ctxEquity = document.getElementById('equityChart').getContext('2d');
const equityChart = new Chart(ctxEquity, {
    type: 'line',
    data: {
        labels: [], // Timestamps
        datasets: [{
            label: 'Cumulative PnL (USDT)',
            data: [], // PnL values
            borderColor: '#00d4ff',
            backgroundColor: 'rgba(0, 212, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHitRadius: 10
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(10, 14, 39, 0.9)',
                titleColor: '#00d4ff',
                bodyColor: '#fff',
                borderColor: '#00d4ff',
                borderWidth: 1
            }
        },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { maxTicksLimit: 8 } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' } }
        }
    }
});

// 2. Gauges (Using Doughnut charts)
const gaugeOptions = {
    responsive: false,
    cutout: '80%',
    plugins: { tooltip: { enabled: false }, legend: { display: false } },
    animation: { animateRotate: true, animateScale: false }
};

const ctxWr = document.getElementById('winrateGauge').getContext('2d');
const wrGauge = new Chart(ctxWr, {
    type: 'doughnut',
    data: { datasets: [{ data: [0, 100], backgroundColor: ['#00ff88', '#27272a'], borderWidth: 0 }] },
    options: gaugeOptions
});

const ctxPf = document.getElementById('pfGauge').getContext('2d');
const pfGauge = new Chart(ctxPf, {
    type: 'doughnut',
    data: { datasets: [{ data: [0, 10], backgroundColor: ['#00d4ff', '#27272a'], borderWidth: 0 }] },
    options: gaugeOptions
});

// 3. Update Time
setInterval(() => {
    document.getElementById('sys-time').innerText = new Date().toLocaleTimeString('en-US', { hour12: false }) + ' ICT';
}, 1000);

// 4. Fetch BTC Ticker
async function pollTicker() {
    try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
        const data = await res.json();
        const last = Number(data.lastPrice);
        const change = Number(data.priceChangePercent);
        document.getElementById('btc-last').innerText = '$' + last.toLocaleString('en-US', {minimumFractionDigits: 2});
        const changeEl = document.getElementById('btc-change');
        changeEl.innerText = change.toFixed(2) + '%';
        changeEl.className = 'value ' + (change >= 0 ? 'green' : 'red');
    } catch(e) {}
}
pollTicker();
setInterval(pollTicker, 3000);

// 5. Fetch Portfolio
async function pollPortfolio() {
    try {
        const res = await fetch('/api/portfolio');
        const data = await res.json();
        if(data.account) {
            document.getElementById('pf-balance').innerText = '$' + Number(data.account.totalWalletBalance).toFixed(2);
            const upnl = Number(data.account.totalUnrealizedProfit);
            const pnlEl = document.getElementById('pf-pnl');
            pnlEl.innerText = (upnl >= 0 ? '+' : '') + upnl.toFixed(2);
            pnlEl.style.color = upnl >= 0 ? 'var(--neon-green)' : 'var(--neon-red)';
            document.getElementById('pf-status').innerText = 'CONNECTED';
            document.getElementById('pf-status').className = 'badge green';
        }
    } catch(e) {
        document.getElementById('pf-status').innerText = 'DISCONNECTED';
        document.getElementById('pf-status').className = 'badge red';
    }
}
pollPortfolio();
setInterval(pollPortfolio, 5000);

// 6. Fetch Trade History & Update Charts
async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        const history = await res.json();
        if(history.length > 0 && !history[0].error) {
            updateDashboard(history);
        }
    } catch(e) {}
}

function updateDashboard(history) {
    const tbody = document.getElementById('history-tbody');
    tbody.innerHTML = '';
    
    let totalPnL = 0;
    let wins = 0;
    let grossProfit = 0;
    let grossLoss = 0;
    
    let labels = [];
    let equityData = [];
    let currentEquity = 0;
    
    // Sort ascending by time for chart
    const sortedHistory = [...history].sort((a,b) => parseInt(a.timestamp) - parseInt(b.timestamp));
    
    sortedHistory.forEach(trade => {
        const pnl = parseFloat(trade.pnl);
        if(pnl !== 0) { // Only settled trades
            currentEquity += pnl;
            labels.push(new Date(parseInt(trade.timestamp)*1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
            equityData.push(currentEquity);
            
            if(pnl > 0) { wins++; grossProfit += pnl; }
            else { grossLoss += Math.abs(pnl); }
        }
    });
    
    // Update Equity Chart
    equityChart.data.labels = labels;
    equityChart.data.datasets[0].data = equityData;
    equityChart.update();
    
    // Reverse for table (newest first)
    history.reverse().forEach(trade => {
        const tr = document.createElement('tr');
        const pnl = parseFloat(trade.pnl);
        const pnlClass = pnl > 0 ? 'green' : (pnl < 0 ? 'red' : '');
        const pnlText = pnl > 0 ? `+$${pnl.toFixed(2)}` : `$${pnl.toFixed(2)}`;
        const sideClass = trade.signal === 'BUY' ? 'green' : 'red';
        
        const td1 = document.createElement('td');
        td1.textContent = new Date(parseInt(trade.timestamp)*1000).toLocaleTimeString();
        const td2 = document.createElement('td');
        td2.className = sideClass;
        td2.textContent = trade.signal;
        const td3 = document.createElement('td');
        td3.textContent = parseFloat(trade.price).toFixed(1);
        const td4 = document.createElement('td');
        td4.textContent = parseFloat(trade.z_ofi).toFixed(2);
        const td5 = document.createElement('td');
        td5.textContent = parseFloat(trade.spread).toFixed(4);
        const td6 = document.createElement('td');
        td6.textContent = trade.strategy || '-';
        const td7 = document.createElement('td');
        td7.className = pnlClass;
        td7.textContent = pnlText;
        
        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);
        tr.appendChild(td4);
        tr.appendChild(td5);
        tr.appendChild(td6);
        tr.appendChild(td7);
        
        tbody.appendChild(tr);
    });
    
    // Update Stats
    const totalSettled = equityData.length;
    document.getElementById('trade-count').innerText = `${totalSettled} TRADES`;
    
    if(totalSettled > 0) {
        document.getElementById('nav-equity').innerText = (currentEquity >= 0 ? '+$' : '-$') + Math.abs(currentEquity).toFixed(2);
        
        const wr = (wins / totalSettled) * 100;
        const pf = grossLoss === 0 ? grossProfit : grossProfit / grossLoss;
        
        document.getElementById('nav-winrate').innerText = wr.toFixed(1) + '%';
        document.getElementById('nav-pf').innerText = pf.toFixed(2);
        
        // Update Gauges
        document.getElementById('gauge-val-wr').innerText = wr.toFixed(0) + '%';
        wrGauge.data.datasets[0].data = [wr, 100-wr];
        wrGauge.data.datasets[0].backgroundColor[0] = wr >= 50 ? '#00ff88' : '#ff3366';
        wrGauge.update();
        
        document.getElementById('gauge-val-pf').innerText = pf.toFixed(2);
        const pfCapped = Math.min(pf, 5);
        pfGauge.data.datasets[0].data = [pfCapped, 5-pfCapped];
        pfGauge.update();
    }
}
fetchHistory();
setInterval(fetchHistory, 5000);

// 7. Live DOM WebSocket
function buildDomRow(bgClass, bidVol, price, askVol, width) {
    const div = document.createElement('div');
    div.className = 'dom-row ' + (bgClass === 'ask' ? 'ask' : 'bid');
    const bar = document.createElement('div');
    bar.className = 'depth-bar';
    bar.style.width = width + '%';
    
    const div1 = document.createElement('div');
    div1.textContent = bidVol;
    const div2 = document.createElement('div');
    div2.className = 'dom-price';
    div2.textContent = price;
    const div3 = document.createElement('div');
    div3.textContent = askVol;
    const div4 = document.createElement('div');
    div4.textContent = bgClass === 'ask' ? 'ASK' : 'BID';
    
    div.appendChild(bar);
    div.appendChild(div1);
    div.appendChild(div2);
    div.appendChild(div3);
    div.appendChild(div4);
    
    return div;
}

let domWs = null;
let reconnectDelay = 3000;
function connectDomWs() {
    domWs = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@depth10@100ms');
    domWs.onopen = () => reconnectDelay = 3000;
    domWs.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if(!data.bids || !data.asks) return;
        
        const domData = document.getElementById('dom-data');
        domData.innerHTML = '';
        
        let maxVol = 0;
        [...data.asks, ...data.bids].forEach(o => maxVol = Math.max(maxVol, parseFloat(o[1])));
        
        // Asks
        for(let i=4; i>=0; i--) {
            const p = parseFloat(data.asks[i][0]).toFixed(1);
            const v = parseFloat(data.asks[i][1]).toFixed(3);
            const w = (v/maxVol)*100;
            domData.appendChild(buildDomRow('ask', '-', p, v, w));
        }
        
        const div = document.createElement('div');
        div.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        div.style.margin = '4px 0';
        domData.appendChild(div);
        
        // Bids
        for(let i=0; i<5; i++) {
            const p = parseFloat(data.bids[i][0]).toFixed(1);
            const v = parseFloat(data.bids[i][1]).toFixed(3);
            const w = (v/maxVol)*100;
            domData.appendChild(buildDomRow('bid', v, p, '-', w));
        }
    };
    domWs.onclose = () => {
        setTimeout(connectDomWs, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
    };
}
connectDomWs();

// 8. Fetch Virtual Trading Room Chat Logs
async function fetchChat() {
    try {
        const res = await fetch('/chat_logs.json?' + new Date().getTime());
        const logs = await res.json();
        const chatBox = document.getElementById('chat-box');
        if(!chatBox) return;
        
        chatBox.innerHTML = '';
        logs.forEach(log => {
            const div = document.createElement('div');
            div.className = 'chat-msg';
            let color = '#8b9bb4';
            if(log.c === 'exec') color = '#00d4ff';
            if(log.c === 'risk') color = '#ff3366';
            if(log.c === 'system') color = '#00ff88';
            const span1 = document.createElement('span');
            span1.style.color = color;
            span1.style.width = '120px';
            span1.style.display = 'inline-block';
            span1.textContent = `[${log.s}]`;
            
            const span2 = document.createElement('span');
            span2.textContent = log.m;
            
            div.appendChild(span1);
            div.appendChild(span2);
            
            chatBox.appendChild(div);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch(e) {}
}
fetchChat();
setInterval(fetchChat, 500); // Increased speed to 500ms
