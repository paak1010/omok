import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.set_page_config(page_title="실시간 스팀릿 오목", layout="centered")

# 1. Firebase URL 가져오기 (주소 끝에 .json이 꼭 있어야 함!)
try:
    DB_URL = st.secrets["firebase_url"]
    if not DB_URL.endswith(".json"):
        DB_URL += "/omok.json"
except KeyError:
    st.error("Secrets에 'firebase_url'을 설정해주세요.")
    st.stop()

st.title("⚫ 진짜 오목 (선 위에 두기) ⚪")

# 2. 내 돌 색상 정하기 (스팀릿 UI 영역)
if 'my_color' not in st.session_state:
    st.session_state.my_color = 1 

col1, col2 = st.columns(2)
with col1:
    if st.button("나는 흑돌(⚫)로 플레이"): st.session_state.my_color = 1
with col2:
    if st.button("나는 백돌(⚪)로 플레이"): st.session_state.my_color = 2

st.write(f"현재 당신은 **{'흑(⚫)' if st.session_state.my_color == 1 else '백(⚪)'}**을 잡고 있습니다.")

# 3. HTML/JS로 찐 오목판 그리기 및 실시간 통신 로직
html_code = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { display: flex; justify-content: center; background-color: #ffffff; margin: 0; font-family: sans-serif; }
    #board-container {
        position: relative;
        width: 600px;
        height: 600px;
        background-color: #DC9A52; /* 나무색 */
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        margin-top: 10px;
        border: 2px solid #553311;
    }
    
    /* 오목판 선 그리기 */
    .line-h { position: absolute; height: 2px; background-color: #333; width: 560px; left: 20px; }
    .line-v { position: absolute; width: 2px; background-color: #333; height: 560px; top: 20px; }
    
    /* 돌이 놓이는 교차점(클릭 영역) */
    .intersection {
        position: absolute;
        width: 34px; 
        height: 34px;
        margin-left: -17px; 
        margin-top: -17px;
        border-radius: 50%;
        cursor: pointer;
        z-index: 10;
        transition: background-color 0.2s;
    }
    
    /* 마우스 올렸을 때 희미하게 표시 */
    .intersection:hover { background-color: rgba(0,0,0,0.2); }
    
    /* 바둑돌 디자인 */
    .stone-black { 
        background-color: #111; 
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5); 
        background-image: radial-gradient(circle at 10px 10px, #555, #000);
    }
    .stone-white { 
        background-color: #f9f9f9; 
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5); 
        background-image: radial-gradient(circle at 10px 10px, #fff, #ccc);
    }
</style>
</head>
<body>

<div id="board-container"></div>

<script>
    const dbUrl = "DB_URL_PLACEHOLDER";
    const myColor = COLOR_PLACEHOLDER;
    const boardSize = 15;
    const step = 40; // 선 간격
    const offset = 20; // 가장자리 여백
    
    const container = document.getElementById("board-container");
    let intersections = [];

    // 1. 가로/세로 선 15개씩 그리기
    for(let i=0; i<boardSize; i++) {
        let lh = document.createElement("div");
        lh.className = "line-h";
        lh.style.top = (offset + i * step) + "px";
        container.appendChild(lh);
        
        let lv = document.createElement("div");
        lv.className = "line-v";
        lv.style.left = (offset + i * step) + "px";
        container.appendChild(lv);
    }
    
    // 2. 15x15 교차점(클릭 버튼) 만들기
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
    
    // 3. 파이어베이스에서 게임 상태 가져오기
    async function fetchState() {
        try {
            let res = await fetch(dbUrl);
            let data = await res.json();
            if(data && data.board) {
                updateBoardUI(data.board);
            }
        } catch(e) { console.error(e); }
    }
    
    // 4. 화면에 돌 그리기
    function updateBoardUI(boardData) {
        for(let r=0; r<boardSize; r++) {
            for(let c=0; c<boardSize; c++) {
                let val = boardData[r][c];
                let dot = intersections[r][c];
                
                // 기존 돌 디자인 초기화
                dot.className = "intersection"; 
                
                // 새 돌 입히기
                if(val === 1) dot.classList.add("stone-black");
                if(val === 2) dot.classList.add("stone-white");
            }
        }
    }
    
    // 5. 돌 놓기 액션
    async function placeStone(r, c) {
        let res = await fetch(dbUrl);
        let data = await res.json();
        
        // 데이터가 없으면 초기화
        if (!data || !data.board) {
            data = { turn: 1, board: Array(15).fill().map(()=>Array(15).fill(0)) };
        }
        
        // 예외 처리
        if (data.board[r][c] !== 0) return; // 이미 돌이 있음
        if (data.turn !== myColor) {
            alert("지금은 당신의 차례가 아닙니다!");
            return;
        }
        
        // 돌 업데이트 후 DB로 전송
        data.board[r][c] = myColor;
        data.turn = (myColor === 1) ? 2 : 1;
        
        await fetch(dbUrl, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        updateBoardUI(data.board); // 내 화면 즉시 반영
    }
    
    // 자바스크립트가 알아서 1초마다 DB를 확인 (스팀릿 새로고침 없음!)
    setInterval(fetchState, 1000);
    fetchState();
</script>
</body>
</html>
"""

# 파이썬 변수를 자바스크립트 코드에 주입
html_code = html_code.replace("DB_URL_PLACEHOLDER", DB_URL).replace("COLOR_PLACEHOLDER", str(st.session_state.my_color))

# 스팀릿에 HTML/JS 삽입 (높이는 바둑판 크기에 맞게 620으로 넉넉히)
components.html(html_code, height=620)

st.divider()

# 게임 초기화 버튼
if st.button("게임 초기화 (새 게임)"):
    empty_data = {
        "board": [[0]*15 for _ in range(15)],
        "turn": 1
    }
    requests.put(DB_URL, data=json.dumps(empty_data))
    st.rerun()
