// Update Clock
setInterval(() => {
    document.getElementById('sys-time').innerText = new Date().toLocaleTimeString('en-US', { hour12: false }) + ' ICT';
}, 1000);

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
