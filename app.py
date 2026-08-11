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
    const boardSize = 15;
    const step = 40; 
    const offset = 20; 
    
    const container = document.getElementById("board-container");
    const turnDisplay = document.getElementById("turn-display");
    const timerDisplay = document.getElementById("timer");
    
    let intersections = [];
    
    // 로컬 상태 관리 (DB 대체)
    let currentData = { 
        turn: 1, 
        board: Array(15).fill().map(()=>Array(15).fill(0)), 
        last_time: Date.now() 
    };

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
    
    // 2. UI 및 턴 업데이트
    function updateBoardUI() {
        turnDisplay.innerText = currentData.turn === 1 ? "현재 턴: 흑(⚫)" : "현재 턴: 백(⚪)";
        
        for(let r=0; r<boardSize; r++) {
            for(let c=0; c<boardSize; c++) {
                let val = currentData.board[r][c];
                let dot = intersections[r][c];
                dot.className = "intersection"; 
                if(val === 1) dot.classList.add("stone-black");
                if(val === 2) dot.classList.add("stone-white");
            }
        }
    }

    // 3. 타이머 로직 (30초 제한)
    function checkTimer() {
        let elapsed = Math.floor((Date.now() - currentData.last_time) / 1000);
        let remain = 30 - elapsed;
        
        if (remain <= 0) {
            timerDisplay.innerText = "시간 초과!";
            passTurn(); // 30초 지나면 턴 넘김
        } else {
            timerDisplay.innerText = `남은 시간: ${remain}초`;
        }
    }

    function passTurn() {
        currentData.turn = (currentData.turn === 1) ? 2 : 1;
        currentData.last_time = Date.now();
        updateBoardUI();
    }
    
    // 4. 금수 체크 로직 (임시)
    function checkForbidden(board, r, c) {
        if (currentData.turn === 2) return false; 
        return false;
    }
    
    // 5. 돌 놓기 액션
    function placeStone(r, c) {
        if (currentData.board[r][c] !== 0) return; 
        
        if (checkForbidden(currentData.board, r, c)) {
            alert("금수 자리입니다! (3-3, 4-4, 또는 장목)"); return;
        }
        
        currentData.board[r][c] = currentData.turn; // 현재 턴의 색깔로 돌 놓기
        currentData.turn = (currentData.turn === 1) ? 2 : 1; // 턴 변경
        currentData.last_time = Date.now(); // 시간 리셋
        
        updateBoardUI(); 
    }
    
    // 1초마다 타이머 확인
    setInterval(checkTimer, 1000);
    updateBoardUI();
</script>
</body>
</html>
