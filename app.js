// Update Clock
setInterval(() => {
    document.getElementById('sys-time').innerText = new Date().toLocaleTimeString('en-US', { hour12: false }) + ' ICT';
}, 1000);



// Live BTC ticker (real Binance REST market data)
const btcLastEl = document.getElementById('btc-last');
const btcChangeEl = document.getElementById('btc-change');

async function pollTicker24h() {
    try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
        const data = await res.json();
        const last = Number(data.lastPrice || 0);
        const change = Number(data.priceChangePercent || 0);

        btcLastEl.textContent = last ? `$${last.toLocaleString('en-US', { maximumFractionDigits: 2 })}` : '--';
        btcChangeEl.textContent = Number.isFinite(change) ? `${change.toFixed(2)}%` : '--';
        btcChangeEl.classList.remove('green');
        btcChangeEl.classList.remove('red');
        btcChangeEl.classList.add(change >= 0 ? 'green' : 'red');
    } catch (err) {
        console.error('Ticker fetch failed:', err);
    }
}

pollTicker24h();
setInterval(pollTicker24h, 3000);
// Connect to REAL Binance WebSocket for Live Order Book (DOM)
const domData = document.getElementById('dom-data');
const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@depth10@100ms');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (!data.bids || !data.asks) return;
    
    domData.innerHTML = '';
    
    // Calculate max volume for visual bars
    let maxVol = 0;
    const allOrders = [...data.asks, ...data.bids];
    allOrders.forEach(order => {
        const vol = parseFloat(order[1]);
        if (vol > maxVol) maxVol = vol;
    });

    // Render Asks (Red) - Top 5
    for(let i = 4; i >= 0; i--) {
        const price = parseFloat(data.asks[i][0]).toFixed(1);
        const vol = parseFloat(data.asks[i][1]).toFixed(3);
        const width = (vol / maxVol) * 100;
        
        const row = document.createElement('div');
        row.className = 'dom-row';
        row.innerHTML = `
            <div class="ask-bg" style="width: ${width}%"></div>
            <div class="bid-vol">-</div>
            <div class="price">${price}</div>
            <div class="ask-vol">${vol}</div>
            <div style="color: var(--neon-red)">ASK</div>
        `;
        domData.appendChild(row);
    }
    
    // Divider
    const divider = document.createElement('div');
    divider.style.borderBottom = '1px solid rgba(255,255,255,0.2)';
    divider.style.margin = '2px 0';
    domData.appendChild(divider);

    // Render Bids (Green) - Top 5
    for(let i = 0; i < 5; i++) {
        const price = parseFloat(data.bids[i][0]).toFixed(1);
        const vol = parseFloat(data.bids[i][1]).toFixed(3);
        const width = (vol / maxVol) * 100;
        
        const row = document.createElement('div');
        row.className = 'dom-row';
        row.innerHTML = `
            <div class="bid-bg" style="width: ${width}%"></div>
            <div class="bid-vol">${vol}</div>
            <div class="price">${price}</div>
            <div class="ask-vol">-</div>
            <div style="color: var(--neon-green)">BID</div>
        `;
        domData.appendChild(row);
    }
};

ws.onerror = (error) => {
    console.error('Binance WebSocket Error:', error);
};

// Multi-Agent Chat Simulation (Fetching from AI Brain)
const chatBox = document.getElementById('chat-box');
let lastChatHash = "";

async function pollAILogs() {
    try {
        // Add timestamp to prevent caching
        const res = await fetch('/chat_logs.json?t=' + new Date().getTime());
        const logs = await res.json();
        
        const currentHash = JSON.stringify(logs);
        if (currentHash !== lastChatHash && logs.length > 0) {
            lastChatHash = currentHash;
            
            chatBox.innerHTML += `<div class="msg" style="color: var(--text-muted);">--- NEW CYCLE ---</div>`;
            
            // Render the messages one by one with a small delay for typing effect
            logs.forEach((msg, index) => {
                setTimeout(() => {
                    chatBox.innerHTML += `
                        <div class="msg">
                            <span class="sender ${msg.c}">[${msg.s}]</span>
                            <span class="text">${msg.m}</span>
                        </div>
                    `;
                    chatBox.scrollTop = chatBox.scrollHeight;
                }, index * 800); // 800ms delay between each line
            });
        }
    } catch (e) {
        // file not ready yet or error, ignore
    }
}

// Poll every 3 seconds
setInterval(pollAILogs, 3000);

// Tab Switching Logic
function switchTab(tabId, event) {
    // Hide all tabs
    document.getElementById('tab-room').style.display = 'none';
    document.getElementById('tab-chart').style.display = 'none';
    
    // Remove active class from all buttons
    const btns = document.querySelectorAll('.tab-btn');
    btns.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById('tab-' + tabId).style.display = tabId === 'room' ? 'grid' : 'block';
    
    // Add active class to clicked button
    event.currentTarget.classList.add('active');
}

// Live Portfolio Polling
var pfBalanceEl = document.getElementById('pf-balance');
var pfPnlEl = document.getElementById('pf-pnl');
var pfPositionsEl = document.getElementById('pf-positions');

async function pollLivePortfolio() {
    try {
        var res = await fetch('/api/portfolio');
        var data = await res.json();

        if (data.account && data.account.totalWalletBalance) {
            var balance = parseFloat(data.account.totalWalletBalance);
            var unrealized = parseFloat(data.account.totalUnrealizedProfit);

            pfBalanceEl.textContent = '$' + balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            var pnlSign = unrealized >= 0 ? '+$' : '-$';
            pfPnlEl.textContent = pnlSign + Math.abs(unrealized).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            pfPnlEl.className = 'value ' + (unrealized >= 0 ? 'green' : 'red');
        } else if (data.account && data.account.status === 'ERROR') {
            pfBalanceEl.textContent = '$0.00';
            pfPnlEl.textContent = '$0.00';
            pfPositionsEl.innerHTML = '<div style="color: var(--neon-red); text-align: center; padding: 20px;">API ERROR: ' + (data.account.msg || 'Check .env keys') + '</div>';
            return;
        } else {
            pfBalanceEl.textContent = '$0.00';
            pfPnlEl.textContent = '$0.00';
        }

        if (data.positions && Array.isArray(data.positions)) {
            var activePositions = data.positions.filter(function(p) { return parseFloat(p.positionAmt) !== 0; });

            if (activePositions.length === 0) {
                pfPositionsEl.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px; font-family: var(--font-mono);">NO OPEN POSITIONS</div>';
            } else {
                pfPositionsEl.innerHTML = '';
                activePositions.forEach(function(p) {
                    var size = parseFloat(p.positionAmt);
                    var isLong = size > 0;
                    var pnl = parseFloat(p.unRealizedProfit);
                    var entry = parseFloat(p.entryPrice);
                    var mark = parseFloat(p.markPrice);
                    var sizeColor = isLong ? 'var(--neon-green)' : 'var(--neon-red)';
                    var pnlColor = pnl >= 0 ? 'var(--neon-green)' : 'var(--neon-red)';
                    var pnlText = (pnl >= 0 ? '+' : '') + pnl.toFixed(2);

                    var row = document.createElement('div');
                    row.className = 'position-row';
                    row.innerHTML = '<div class="symbol">' + p.symbol + ' ' + (p.leverage || '') + 'x</div>' +
                        '<div class="size" style="color:' + sizeColor + '">' + size + '</div>' +
                        '<div>' + entry.toFixed(1) + '</div>' +
                        '<div>' + mark.toFixed(1) + '</div>' +
                        '<div style="color:' + pnlColor + '">' + pnlText + '</div>';
                    pfPositionsEl.appendChild(row);
                });
            }
        } else {
            pfPositionsEl.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px; font-family: var(--font-mono);">NO OPEN POSITIONS</div>';
        }
    } catch (e) {
        console.error('Portfolio fetch failed', e);
    }
}

// Poll portfolio every 3 seconds
pollLivePortfolio();
setInterval(pollLivePortfolio, 3000);
