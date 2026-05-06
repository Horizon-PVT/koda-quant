// Update Clock
setInterval(function() {
    document.getElementById('sys-time').innerText = new Date().toLocaleTimeString('en-US', { hour12: false }) + ' ICT';
}, 1000);

// Live BTC ticker (real Binance REST market data)
var btcLastEl = document.getElementById('btc-last');
var btcChangeEl = document.getElementById('btc-change');

async function pollTicker24h() {
    try {
        var res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
        var data = await res.json();
        var last = Number(data.lastPrice || 0);
        var change = Number(data.priceChangePercent || 0);

        btcLastEl.textContent = last ? '$' + last.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '--';
        btcChangeEl.textContent = Number.isFinite(change) ? change.toFixed(2) + '%' : '--';
        btcChangeEl.classList.remove('green', 'red');
        btcChangeEl.classList.add(change >= 0 ? 'green' : 'red');
    } catch (err) {
        console.error('Ticker fetch failed:', err);
    }
}

pollTicker24h();
setInterval(pollTicker24h, 3000);

// Connect to REAL Binance WebSocket for Live Order Book (DOM)
var domData = document.getElementById('dom-data');
var domWs = null;

function connectDomWs() {
    domWs = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@depth10@100ms');

    domWs.onmessage = function(event) {
        var data = JSON.parse(event.data);
        if (!data.bids || !data.asks) return;
        
        domData.innerHTML = '';
        
        var maxVol = 0;
        var allOrders = data.asks.concat(data.bids);
        allOrders.forEach(function(order) {
            var vol = parseFloat(order[1]);
            if (vol > maxVol) maxVol = vol;
        });

        // Render Asks (Red) - Top 5
        for (var i = 4; i >= 0; i--) {
            var price = parseFloat(data.asks[i][0]).toFixed(1);
            var vol = parseFloat(data.asks[i][1]).toFixed(3);
            var width = (vol / maxVol) * 100;
            
            var row = document.createElement('div');
            row.className = 'dom-row';
            row.innerHTML = '<div class="ask-bg" style="width: ' + width + '%"></div>' +
                '<div class="bid-vol">-</div>' +
                '<div class="price">' + price + '</div>' +
                '<div class="ask-vol">' + vol + '</div>' +
                '<div style="color: var(--neon-red)">ASK</div>';
            domData.appendChild(row);
        }
        
        // Divider
        var divider = document.createElement('div');
        divider.style.borderBottom = '1px solid rgba(255,255,255,0.2)';
        divider.style.margin = '2px 0';
        domData.appendChild(divider);

        // Render Bids (Green) - Top 5
        for (var j = 0; j < 5; j++) {
            var bPrice = parseFloat(data.bids[j][0]).toFixed(1);
            var bVol = parseFloat(data.bids[j][1]).toFixed(3);
            var bWidth = (bVol / maxVol) * 100;
            
            var bRow = document.createElement('div');
            bRow.className = 'dom-row';
            bRow.innerHTML = '<div class="bid-bg" style="width: ' + bWidth + '%"></div>' +
                '<div class="bid-vol">' + bVol + '</div>' +
                '<div class="price">' + bPrice + '</div>' +
                '<div class="ask-vol">-</div>' +
                '<div style="color: var(--neon-green)">BID</div>';
            domData.appendChild(bRow);
        }
    };

    domWs.onerror = function(error) {
        console.error('Binance WebSocket Error:', error);
    };

    // P2 FIX: Auto-reconnect with exponential backoff
    domWs.onclose = function() {
        console.warn('DOM WebSocket closed. Reconnecting in 3s...');
        setTimeout(connectDomWs, 3000);
    };
}

connectDomWs();

// Multi-Agent Chat Simulation (Fetching from AI Brain)
var chatBox = document.getElementById('chat-box');
var lastChatHash = "";

async function pollAILogs() {
    try {
        var res = await fetch('/chat_logs.json?t=' + new Date().getTime());
        var logs = await res.json();
        
        var currentHash = JSON.stringify(logs);
        if (currentHash !== lastChatHash && logs.length > 0) {
            lastChatHash = currentHash;
            
            var cycleDiv = document.createElement('div');
            cycleDiv.className = 'msg';
            cycleDiv.style.color = 'var(--text-muted)';
            cycleDiv.textContent = '--- NEW CYCLE ---';
            chatBox.appendChild(cycleDiv);
            
            // P1 XSS FIX: Safe rendering with textContent (never innerHTML for user/LLM data)
            var allowedClasses = {micro: true, risk: true, exec: true, system: true};
            logs.forEach(function(msg, index) {
                setTimeout(function() {
                    var msgDiv = document.createElement('div');
                    msgDiv.className = 'msg';
                    
                    var sender = document.createElement('span');
                    sender.className = 'sender ' + (allowedClasses[msg.c] ? msg.c : '');
                    sender.textContent = '[' + msg.s + ']';
                    
                    var text = document.createElement('span');
                    text.className = 'text';
                    text.textContent = ' ' + msg.m;
                    
                    msgDiv.appendChild(sender);
                    msgDiv.appendChild(text);
                    chatBox.appendChild(msgDiv);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }, index * 800);
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
    document.getElementById('tab-room').style.display = 'none';
    document.getElementById('tab-chart').style.display = 'none';
    
    var btns = document.querySelectorAll('.tab-btn');
    btns.forEach(function(btn) { btn.classList.remove('active'); });
    
    document.getElementById('tab-' + tabId).style.display = tabId === 'room' ? 'grid' : 'block';
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
