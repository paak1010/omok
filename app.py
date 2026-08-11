<!DOCTYPE html>
<html>
<head>
<style>
    body { display: flex; flex-direction: column; align-items: center; background-color: #ffffff; margin: 0; font-family: sans-serif; }
    
    /* 타이머 및 상태 표시줄 */
    #status-bar {
        width: 600px;
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
        font-size: 18px;
        font-weight: bold;
    }
    #timer { color: #d32f2f; }

    #board-container {
        position: relative;
        width: 600px;
        height: 600px;
        background-color: #DC9A52; 
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        margin-top: 10px;
        border: 2px solid #553311;
    }
    
    .line-h { position: absolute; height: 2px; background-color: #333; width: 560px; left: 20px; }
    .line-v { position: absolute; width: 2px; background-color: #333; height: 560px; top: 20px; }
    
    .intersection {
        position: absolute; width: 34px; height: 34px;
        margin-left: -17px; margin-top: -17px;
        border-radius: 50%; cursor: pointer; z-index: 10;
        transition: background-color 0.2s;
    }
    .intersection:hover { background-color: rgba(0,0,0,0.2); }
    
    .stone-black { 
        background-color: #111; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); 
        background-image: radial-gradient(circle at 10px 10px, #555, #000);
    }
    .stone-white { 
        background-color: #f9f9f9; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); 
        background-image: radial-gradient(circle at 10px 10px, #fff, #ccc);
    }
</style>
</head>
<body>

<div id="status-bar">
    <div id="turn-display">현재 턴: 흑(⚫)</div>
    <div id="timer">남은 시간: 30초</div>
</div>
<div id="board-container"></div>

<script>
    const dbUrl = "DB_URL_PLACEHOLDER";
    const myColor = COLOR_PLACEHOLDER;
    const boardSize = 15;
    const step = 40; 
    const offset = 20; 
    
    const container = document.getElementById("board-container");
    const turnDisplay = document.getElementById("turn-display");
    const timerDisplay = document.getElementById("timer");
    
    let intersections = [];
    let currentData = null;

    // 1. 바둑판 그리기
    for(let i=0; i<boardSize; i++) {
        let lh = document.createElement("div"); lh.className = "line-h"; lh.style.top = (offset + i * step) + "px"; container.appendChild(lh);
        let lv = document.createElement("div"); lv.className = "line-v"; lv.style.left = (offset + i * step) + "px"; container.appendChild(lv);
    }
    
    for(let r=0; r<boardSize; r++) {
        intersections[r] = [];
        for(let c=0; c<boardSize; c++) {
            let dot = document.createElement("div");
            dot.className = "intersection";
            dot.style.top = (offset + r * step) + "px"; dot.style.left = (offset + c * step) + "px";
            dot.onclick = () => placeStone(r, c);
            container.appendChild(dot); intersections[r][c] = dot;
        }
    }
    
    // 2. DB 상태 가져오기
    async function fetchState() {
        try {
            let res = await fetch(dbUrl);
            currentData = await res.json();
            if(currentData && currentData.board) {
                updateBoardUI(currentData);
                checkTimer(currentData);
            }
        } catch(e) { console.error(e); }
    }
    
    // 3. UI 및 턴 업데이트
    function updateBoardUI(data) {
        turnDisplay.innerText = data.turn === 1 ? "현재 턴: 흑(⚫)" : "현재 턴: 백(⚪)";
        
        for(let r=0; r<boardSize; r++) {
            for(let c=0; c<boardSize; c++) {
                let val = data.board[r][c];
                let dot = intersections[r][c];
                dot.className = "intersection"; 
                if(val === 1) dot.classList.add("stone-black");
                if(val === 2) dot.classList.add("stone-white");
            }
        }
    }

    // 4. 타이머 로직 (30초 제한)
    function checkTimer(data) {
        if (!data.last_time) return;
        
        let elapsed = Math.floor((Date.now() - data.last_time) / 1000);
        let remain = 30 - elapsed;
        
        if (remain <= 0) {
            timerDisplay.innerText = "시간 초과!";
            // 시간 초과 시 턴 넘기기 로직 (원한다면 패배 처리로 변경 가능)
            if (data.turn === myColor) passTurn(data);
        } else {
            timerDisplay.innerText = `남은 시간: ${remain}초`;
        }
    }

    async function passTurn(data) {
        data.turn = (data.turn === 1) ? 2 : 1;
        data.last_time = Date.now();
        await fetch(dbUrl, { method: 'PUT', body: JSON.stringify(data) });
        fetchState();
    }
    
    // 5. 렌주룰(금수) 체크 함수 (흑돌만 적용)
    function checkForbidden(board, r, c) {
        if (myColor === 2) return false; // 백돌은 금수 없음
        
        // TODO: 완벽한 3-3, 4-4 렌주룰 알고리즘은 매우 복잡하므로 
        // 여기에 8방향 탐색 알고리즘을 추가해야 합니다.
        // 임시로 장목(6목 이상)만 금지하는 간단한 로직 예시를 추가할 수 있습니다.
        
        return false; // 금수면 true 반환
    }
    
    // 6. 돌 놓기 액션
    async function placeStone(r, c) {
        if (!currentData || !currentData.board) {
            currentData = { turn: 1, board: Array(15).fill().map(()=>Array(15).fill(0)), last_time: Date.now() };
        }
        
        if (currentData.board[r][c] !== 0) return; 
        if (currentData.turn !== myColor) {
            alert("지금은 당신의 차례가 아닙니다!"); return;
        }

        // 금수 자리인지 확인 (흑돌)
        if (checkForbidden(currentData.board, r, c)) {
            alert("금수 자리입니다! (3-3, 4-4, 또는 장목)"); return;
        }
        
        currentData.board[r][c] = myColor;
        currentData.turn = (myColor === 1) ? 2 : 1;
        currentData.last_time = Date.now(); // 시간 리셋
        
        await fetch(dbUrl, { method: 'PUT', body: JSON.stringify(currentData) });
        updateBoardUI(currentData); 
    }
    
    setInterval(fetchState, 1000);
    fetchState();
</script>
</body>
</html>
