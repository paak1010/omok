import streamlit as st
import requests
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="실시간 스팀릿 오목", layout="centered")

# Streamlit Secrets에서 Firebase DB URL 가져오기
# 예: "https://my-project-default-rtdb.firebaseio.com/omok.json"
try:
    DB_URL = st.secrets["firebase_url"]
except KeyError:
    st.error("Streamlit Secrets에 'firebase_url'을 설정해주세요.")
    st.stop()

# 상대방 수를 확인하기 위해 2초마다 화면 자동 새로고침
st_autorefresh(interval=2000, key="data_refresh")

def fetch_game_state():
    """Firebase에서 현재 게임 상태 불러오기"""
    response = requests.get(DB_URL)
    data = response.json()
    if data:
        return data
    # DB가 비어있으면 초기 상태 반환
    return {"board": [[0]*15 for _ in range(15)], "turn": 1}

def update_game_state(new_board, next_turn):
    """Firebase에 새로운 게임 상태 저장하기"""
    data = {"board": new_board, "turn": next_turn}
    requests.put(DB_URL, data=json.dumps(data))

# 게임 상태 초기화
state = fetch_game_state()
board = state["board"]
current_turn = state["turn"]

st.title("⚫ 실시간 스팀릿 오목 ⚪")
st.write(f"**현재 차례:** {'흑(⚫)' if current_turn == 1 else '백(⚪)'}")

# 로컬 플레이어 색상 선택
if 'my_color' not in st.session_state:
    st.session_state.my_color = 1 

col1, col2 = st.columns(2)
with col1:
    if st.button("나는 흑돌(⚫)"): st.session_state.my_color = 1
with col2:
    if st.button("나는 백돌(⚪)"): st.session_state.my_color = 2

st.divider()

# 15x15 보드 렌더링
for r in range(15):
    cols = st.columns(15)
    for c in range(15):
        cell_value = board[r][c]
        
        if cell_value == 1: icon = "⚫"
        elif cell_value == 2: icon = "⚪"
        else: icon = "➕"
            
        with cols[c]:
            # 빈 칸이 아니거나, 내 턴이 아니면 버튼 비활성화
            disabled = (cell_value != 0) or (current_turn != st.session_state.my_color)
            
            if st.button(icon, key=f"{r}_{c}", disabled=disabled):
                # 돌을 놓고 DB 업데이트
                board[r][c] = st.session_state.my_color
                next_turn = 2 if st.session_state.my_color == 1 else 1
                update_game_state(board, next_turn)
                st.rerun()

st.divider()
if st.button("게임 초기화 (보드 비우기)"):
    empty_board = [[0]*15 for _ in range(15)]
    update_game_state(empty_board, 1)
    st.rerun()
