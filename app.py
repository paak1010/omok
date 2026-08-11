import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.set_page_config(page_title="실시간 스팀릿 오목", layout="centered")

try:
    DB_URL = st.secrets["firebase_url"]
    if not DB_URL.endswith(".json"):
        DB_URL += "/omok.json"
except KeyError:
    st.error("Secrets에 'firebase_url'을 설정해주세요.")
    st.stop()

st.title("⚫ 렌주룰 오목 (금수 표시 추가) ⚪")

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

    #board-container {
        position: relative; width: 600px; height: 600px;
        background-color: #DC9A52; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); border: 2px solid #553311;
    }
    
    .line-h { position: absolute; height: 2px; background-color: #333; width: 560px; left: 20px; }
    .line-v { position: absolute; width: 2px; background-color: #333; height: 560px; top: 20px; }
    
    .intersection {
        position: absolute; width: 34px; height: 34px;
        margin-left: -17px; margin-top: -17px;
        border-radius: 50%; cursor: pointer; z-index: 10;
    }
    .intersection:hover { background-color: rgba(0,0,0,0.2); }
    
    /* 금수(✕) 표시 디자인 */
    .forbidden::after {
        content: '✕';
        color: #d93025;
        font-size: 24px;
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none; /* 클릭 방해 안함 */
    }
    
    .stone-black { background-color: #111; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); background-image: radial-gradient(circle at 10px 10px, #555, #000); }
    .stone-white { background-color: #f9f9f9; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); background-image: radial-gradient(circle at 10px 10px, #fff, #ccc); }
</style>
</head>
<body>

<div id="status-text">게임 데이터를 불러오는 중...</div>
<div id="board-container"></div>

<script>
    const dbUrl = "DB_URL_PLACEHOLDER";
    const myColor = COLOR_PLACEHOLDER;
    const boardSize = 15;
    const step = 40; const offset = 20; 
    
    const container = document.getElementById("board-container");
    const statusText = document.getElementById("status-text");
    let intersections = [];

    // 바둑판 생성
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
            dot.onclick = () => placeStone(r, c);
            container.appendChild(dot);
            intersections[r][c] = dot;
        }
    }
    
    // 승리 조건 체크
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
            if (count === 5) return true; // 백은 6목도 승리지만, 여기선 기본 5목만 체크
        }
        return false;
    }

    // ★ 렌주룰 (금수) 판별 함수 ★
    function isForbidden(board, r, c) {
        if (myColor === 2) return false; // 백돌은 금수가 없음

        let lines = [];
        let dr = [0, 1, 1, 1];
        let dc = [1, 0, 1, -1];
        
        // 4방향으로 돌을 나열해서 문자열로 만듦 (E:빈칸, B:흑돌, W:백돌/벽)
        for(let i=0; i<4; i++) {
            let str = "";
            for(let j=-5; j<=5; j++) {
                let nr = r + j*dr[i]; let nc = c + j*dc[i];
                if(j === 0) str += "B"; // 현재 놓을 자리
                else if(nr<0 || nr>=15 || nc<0 || nc>=15) str += "W";
                else if(board[nr][nc]===1) str += "B";
                else if(board[nr][nc]===2) str += "W";
                else str += "E";
            }
            lines.push(str);
        }

        // 1. 5목 완성인가? (승리 우선이므로 금수 아님)
        let isFive = lines.some(l => l.includes("BBBBB") && !l.includes("BBBBBB"));
        if (isFive) return false; 

        // 2. 장목 (6목 이상) - 흑돌은 무조건 금수
        let isOverline = lines.some(l => l.includes("BBBBBB"));
        if (isOverline) return true; 

        let fourCount = 0;
        let openThreeCount = 0;

        lines.forEach(l => {
            // 4-4 체크 (빈칸 E를 채웠을 때 5목이 되는 자리가 있는지 확인)
            let makeFiveSpots = 0;
            for(let i=0; i<l.length; i++) {
                if (l[i] === 'E') {
                    let temp = l.substring(0, i) + 'B' + l.substring(i+1);
                    if (temp.includes("BBBBB") && !temp.includes("BBBBBB")) makeFiveSpots++;
                }
            }
            if (makeFiveSpots > 0) fourCount++;

            // 3-3 체크 (열린 3 패턴 확인)
            let isOpen3 = false;
            if (/(?<!B)EEBBBE(?!B)/.test(l)) isOpen3 = true;
            if (/(?<!B)EBBBEE(?!B)/.test(l)) isOpen3 = true;
            if (/(?<!B)EBEBBE(?!B)/.test(l)) isOpen3 = true;
            if (/(?<!B)EBBEBE(?!B)/.test(l)) isOpen3 = true;
            if (isOpen3) openThreeCount++;
        });

        // 쌍사(4-4) 이거나 쌍삼(3-3) 이면 금수
        if (fourCount >= 2) return true; 
        if (openThreeCount >= 2) return true; 

        return false;
    }

    async function fetchState() {
        try {
            let res = await fetch(dbUrl);
            let data = await res.json();
            if(data && data.board) updateBoardUI(data);
        } catch(e) { console.error(e); }
    }
    
    function updateBoardUI(data) {
        let boardData = data.board;
        
        if (data.winner && data.winner !== 0) {
            statusText.innerHTML = data.winner === 1 ? "🎉 <b>흑돌(⚫) 승리!</b>" : "🎉 <b>백돌(⚪) 승리!</b>";
            statusText.style.color = "#d93025";
        } else {
            let isMyTurn = (data.turn === myColor);
            statusText.innerHTML = (isMyTurn ? "➡️ 내 차례입니다! " : "⏳ 상대방 대기 중... ") + 
                                   (data.turn === 1 ? "흑(⚫)" : "백(⚪)");
            statusText.style.color = isMyTurn ? "#1a73e8" : "#000";
        }

        // 바둑판 다시 그리기
        for(let r=0; r<boardSize; r++) {
            for(let c=0; c<boardSize; c++) {
                let val = boardData[r][c];
                let dot = intersections[r][c];
                
                // 기존 클래스 싹 비우기
                dot.className = "intersection"; 
                
                if(val === 1) {
                    dot.classList.add("stone-black");
                } else if(val === 2) {
                    dot.classList.add("stone-white");
                } else {
                    // 빈 칸이고, 게임이 안 끝났고, 내(흑돌) 차례일 때 금수 계산
                    if (myColor === 1 && data.turn === 1 && !data.winner) {
                        if (isForbidden(boardData, r, c)) {
                            dot.classList.add("forbidden");
                        }
                    }
                }
            }
        }
    }
    
    async function placeStone(r, c) {
        let res = await fetch(dbUrl);
        let data = await res.json();
        
        if (!data || !data.board) return;
        if (data.winner && data.winner !== 0) {
            alert("이미 게임이 종료되었습니다."); return;
        }
        if (data.board[r][c] !== 0) return; 
        if (data.turn !== myColor) {
            alert("지금은 당신의 차례가 아닙니다!"); return;
        }

        // 금수 자리 방어벽
        if (myColor === 1 && isForbidden(data.board, r, c)) {
            alert("이곳은 금수(3-3, 4-4, 6목) 자리라서 흑돌을 둘 수 없습니다!");
            return;
        }
        
        data.board[r][c] = myColor;
        
        if (checkWin(data.board, r, c, myColor)) {
            data.winner = myColor; 
        } else {
            data.turn = (myColor === 1) ? 2 : 1; 
        }
        
        await fetch(dbUrl, { method: 'PUT', body: JSON.stringify(data) });
        updateBoardUI(data); 
    }
    
    setInterval(fetchState, 1000);
    fetchState();
</script>
</body>
</html>
"""

html_code = html_code.replace("DB_URL_PLACEHOLDER", DB_URL).replace("COLOR_PLACEHOLDER", str(st.session_state.my_color))

components.html(html_code, height=670)

st.divider()

if st.button("🔄 게임 초기화 (새 게임 시작)"):
    empty_data = {
        "board": [[0]*15 for _ in range(15)],
        "turn": 1,
        "winner": 0
    }
    requests.put(DB_URL, data=json.dumps(empty_data))
    st.rerun()
