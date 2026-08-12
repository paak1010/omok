import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.set_page_config(page_title="멘소래담 오목", layout="wide")

try:
    DB_URL = st.secrets["firebase_url"]
    if not DB_URL.endswith(".json"):
        DB_URL += "/omok.json"
except KeyError:
    st.error("Secrets에 'firebase_url'을 설정해주세요.")
    st.stop()

st.title("⚫ 멘소래담 오목 ⚪")

if 'my_color' not in st.session_state:
    st.session_state.my_color = 1 

col1, col2 = st.columns(2)
with col1:
    if st.button("나는 흑돌(⚫)로 플레이"): st.session_state.my_color = 1
with col2:
    if st.button("나는 백돌(⚪)로 플레이"): st.session_state.my_color = 2

html_code = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { display: flex; flex-direction: column; align-items: center; background-color: #ffffff; margin: 0; font-family: sans-serif; }
    
    #status-text {
        font-size: 20px; font-weight: bold; margin: 15px 0; height: 30px;
    }

    /* 19x19 사이즈에 맞춰 760px로 확장 */
    #board-container {
        position: relative; width: 760px; height: 760px;
        background-color: #DC9A52; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); border: 2px solid #553311;
    }
    
    /* 선 길이 19x19에 맞춰 720px로 확장 */
    .line-h { position: absolute; height: 2px; background-color: #333; width: 720px; left: 20px; }
    .line-v { position: absolute; width: 2px; background-color: #333; height: 720px; top: 20px; }
    
    .intersection {
        position: absolute; width: 34px; height: 34px;
        margin-left: -17px; margin-top: -17px;
        border-radius: 50%; cursor: pointer; z-index: 10;
    }
    .intersection:hover { background-color: rgba(0,0,0,0.1); }
    
    #submit-btn {
        margin-top: 20px; padding: 12px 50px; font-size: 20px; font-weight: bold;
        color: white; background-color: #1a73e8; border: none; border-radius: 8px;
        cursor: pointer; transition: 0.2s; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    #submit-btn:disabled { background-color: #cccccc; cursor: not-allowed; box-shadow: none; color: #777;}
    #submit-btn:hover:not(:disabled) { background-color: #1557b0; }

    .forbidden::after {
        content: '✕'; color: #d93025; font-size: 24px;
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        pointer-events: none;
    }
    
    .last-move::after {
        content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 12px; height: 12px; background-color: #ff3333; border-radius: 50%; pointer-events: none;
    }
    
    .stone-black { background-color: #111; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); background-image: radial-gradient(circle at 10px 10px, #555, #000); }
    .stone-white { background-color: #f9f9f9; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); background-image: radial-gradient(circle at 10px 10px, #fff, #ccc); }
    
    .preview-black { background-color: #111; opacity: 0.5; }
    .preview-white { background-color: #f9f9f9; opacity: 0.5; }
</style>
</head>
<body>

<div id="status-text">게임 데이터를 불러오는 중...</div>
<div id="board-container"></div>
<button id="submit-btn" onclick="submitMove()" disabled>제출 </button>

<script>
    const dbUrl = "DB_URL_PLACEHOLDER";
    const myColor = COLOR_PLACEHOLDER;
    const boardSize = 19; // 19x19로 변경
    const step = 40; const offset = 20; 
    
    const container = document.getElementById("board-container");
    const statusText = document.getElementById("status-text");
    const submitBtn = document.getElementById("submit-btn");
    
    let intersections = [];
    let currentDataCache = null; 
    let selectedSpot = null;     

    for(let i=0; i<boardSize; i++) {
        let lh = document.createElement("div"); lh.className = "line-h"; lh.style.top = (offset + i * step) + "px"; container.appendChild(lh);
        let lv = document.createElement("div"); lv.className = "line-v"; lv.style.left = (offset + i * step) + "px"; container.appendChild(lv);
    }
    
    for(let r=0; r<boardSize; r++) {
        intersections[r] = [];
        for(let c=0; c<boardSize; c++) {
            let dot = document.createElement("div");
            dot.className = "intersection";
            dot.style.top = (offset + r * step) + "px";
            dot.style.left = (offset + c * step) + "px";
            dot.onclick = () => selectSpot(r, c); 
            container.appendChild(dot);
            intersections[r][c] = dot;
        }
    }
    
    function checkWin(board, r, c, color) {
        const directions = [ [[0, 1], [0, -1]], [[1, 0], [-1, 0]], [[1, 1], [-1, -1]], [[1, -1], [-1, 1]] ];
        for (let d = 0; d < 4; d++) {
            let count = 1;
            for (let i = 0; i < 2; i++) {
                let dr = directions[d][i][0]; let dc = directions[d][i][1];
                let nr = r + dr; let nc = c + dc;
                while (nr >= 0 && nr < boardSize && nc >= 0 && nc < boardSize && board[nr][nc] === color) {
                    count++; nr += dr; nc += dc;
                }
            }
            if (count === 5) return true; 
        }
        return false;
    }

    function isForbidden(board, r, c) {
        if (myColor === 2) return false; 
        let lines = [];
        let dr = [0, 1, 1, 1]; let dc = [1, 0, 1, -1];
        
        for(let i=0; i<4; i++) {
            let str = "";
            for(let j=-5; j<=5; j++) {
                let nr = r + j*dr[i]; let nc = c + j*dc[i];
                if(j === 0) str += "B"; 
                // 15에서 boardSize(19)로 변경
                else if(nr<0 || nr>=boardSize || nc<0 || nc>=boardSize) str += "W";
                else if(board[nr][nc]===1) str += "B";
                else if(board[nr][nc]===2) str += "W";
                else str += "E";
            }
            lines.push(str);
        }

        let isFive = lines.some(l => l.includes("BBBBB") && !l.includes("BBBBBB"));
        if (isFive) return false; 

        let isOverline = lines.some(l => l.includes("BBBBBB"));
        if (isOverline) return true; 

        let fourCount = 0; let openThreeCount = 0;
        lines.forEach(l => {
            let makeFiveSpots = 0;
            for(let i=0; i<l.length; i++) {
                if (l[i] === 'E') {
                    let temp = l.substring(0, i) + 'B' + l.substring(i+1);
                    if (temp.includes("BBBBB") && !temp.includes("BBBBBB")) makeFiveSpots++;
                }
            }
            if (makeFiveSpots > 0) fourCount++;

            let isOpen3 = false;
            if (/(?<!B)EEBBBE(?!B)/.test(l) || /(?<!B)EBBBEE(?!B)/.test(l) || /(?<!B)EBEBBE(?!B)/.test(l) || /(?<!B)EBBEBE(?!B)/.test(l)) isOpen3 = true;
            if (isOpen3) openThreeCount++;
        });

        if (fourCount >= 2 || openThreeCount >= 2) return true; 
        return false;
    }

    async function fetchState() {
        try {
            let res = await fetch(dbUrl);
            let data = await res.json();
            if(data && data.board) {
                currentDataCache = data;
                
                if(selectedSpot) {
                    if (data.turn !== myColor || data.board[selectedSpot.r][selectedSpot.c] !== 0) {
                        selectedSpot = null; 
                    }
                }
                updateBoardUI();
            }
        } catch(e) { console.error(e); }
    }
    
    function updateBoardUI() {
        if(!currentDataCache) return;
        let data = currentDataCache;
        let boardData = data.board;
        
        if (data.winner && data.winner !== 0) {
            statusText.innerHTML = data.winner === 1 ? "🎉 <b>흑돌(⚫) 승리!</b>" : "🎉 <b>백돌(⚪) 승리!</b>";
            statusText.style.color = "#d93025";
            submitBtn.disabled = true;
        } else {
            let isMyTurn = (data.turn === myColor);
            statusText.innerHTML = (isMyTurn ? "➡️ 내 차례입니다! " : "⏳ 상대방 대기 중... ") + (data.turn === 1 ? "흑(⚫)" : "백(⚪)");
            statusText.style.color = isMyTurn ? "#1a73e8" : "#000";
            
            if (isMyTurn && selectedSpot) submitBtn.disabled = false;
            else submitBtn.disabled = true;
        }

        for(let r=0; r<boardSize; r++) {
            for(let c=0; c<boardSize; c++) {
                let val = boardData[r][c];
                let dot = intersections[r][c];
                
                dot.className = "intersection"; 
                
                if(val === 1) {
                    dot.classList.add("stone-black");
                } else if(val === 2) {
                    dot.classList.add("stone-white");
                } else {
                    if (myColor === 1 && data.turn === 1 && !data.winner) {
                        if (isForbidden(boardData, r, c)) dot.classList.add("forbidden");
                    }
                }
                
                if (data.lastMove && data.lastMove.r === r && data.lastMove.c === c) {
                    dot.classList.add("last-move");
                }
                
                if (selectedSpot && selectedSpot.r === r && selectedSpot.c === c) {
                    dot.classList.add(myColor === 1 ? "preview-black" : "preview-white");
                }
            }
        }
    }
    
    function selectSpot(r, c) {
        if (!currentDataCache) return;
        let data = currentDataCache;
        
        if (data.winner && data.winner !== 0) return; 
        if (data.turn !== myColor) return;            
        if (data.board[r][c] !== 0) return;           
        
        if (myColor === 1 && isForbidden(data.board, r, c)) {
            alert("이곳은 금수(3-3, 4-4, 6목) 자리입니다!");
            return;
        }
        
        selectedSpot = {r: r, c: c};
        updateBoardUI(); 
    }

    async function submitMove() {
        if(!selectedSpot || !currentDataCache) return;
        
        submitBtn.disabled = true; 
        let r = selectedSpot.r;
        let c = selectedSpot.c;
        
        let res = await fetch(dbUrl);
        let data = await res.json();
        
        if (data.board[r][c] !== 0 || data.turn !== myColor) {
            alert("유효하지 않은 수입니다. 바둑판 상황이 변경되었습니다.");
            selectedSpot = null; fetchState(); return;
        }

        data.board[r][c] = myColor;
        data.lastMove = {r: r, c: c}; 
        
        if (checkWin(data.board, r, c, myColor)) {
            data.winner = myColor; 
        } else {
            data.turn = (myColor === 1) ? 2 : 1; 
        }
        
        selectedSpot = null;
        await fetch(dbUrl, { method: 'PUT', body: JSON.stringify(data) });
        currentDataCache = data;
        updateBoardUI(); 
    }
    
    setInterval(fetchState, 1000);
    fetchState();
</script>
</body>
</html>
"""

html_code = html_code.replace("DB_URL_PLACEHOLDER", DB_URL).replace("COLOR_PLACEHOLDER", str(st.session_state.my_color))

# 19x19 화면 크기 확장에 맞춰 컴포넌트 전체 높이 여유있게 늘림 (750 -> 950)
components.html(html_code, height=950) 

st.divider()

if st.button("🔄 게임 초기화 (새 게임 시작)"):
    empty_data = {
        "board": [[0]*19 for _ in range(19)], # 초기화 시 파이썬 배열도 19x19로 변경
        "turn": 1,
        "winner": 0,
        "lastMove": None
    }
    requests.put(DB_URL, data=json.dumps(empty_data))
    st.rerun()
