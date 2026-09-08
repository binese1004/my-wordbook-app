import streamlit as st
import random
from openai import OpenAI
from gtts import gTTS
import base64
import os

st.set_page_config(page_title="아이 전용 영어 단어장", layout="centered")

st.title("🔤 하루 15개 영어 단어 퀴즈")

# API 키 입력받기
api_key = st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# 1. 사진 업로드
uploaded_file = st.file_uploader("단어장 사진을 올려주세요", type=["jpg", "png", "jpeg"])

if uploaded_file and api_key and not st.session_state.word_list:
    if st.button("사진에서 단어 추출하고 순서 섞기"):
        client = OpenAI(api_key=api_key)
        
        # 이미지 읽기
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        with st.spinner("사진에서 단어를 추출하는 중입니다..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "이 이미지에 있는 영어 단어 15개와 그 뜻을 추출해서 다른 설명 없이 '단어: 뜻' 형식으로 한 줄씩만 출력해줘."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            raw_text = response.choices[0].message.content
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            # 순서 무작위 섞기 (중복 원천 차단)
            random.shuffle(lines)
            st.session_state.word_list = lines
            st.session_state.current_index = 0
            st.rerun()

# 2. 단어 테스트 진행
if st.session_state.word_list:
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.write(f"### 진행 상황: {idx + 1} / {total}")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 음성 생성 (천천히 읽기 slow=True)
    tts = gTTS(text=eng_word, lang='en', slow=True)
    tts.save("temp.mp3")
    
    # 음성 자동 재생
    audio_file = open("temp.mp3", "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    
    st.divider()
    
    # 정답 확인 버튼
    if st.checkbox("👁️ 철자 및 뜻 확인하기"):
        st.success(f"**{current_pair}**")
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전 단어") and idx > 0:
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if st.button("다음 단어 ➡️") and idx < total - 1:
            st.session_state.current_index += 1
            st.rerun()
            
    if st.button("🔄 새로운 사진으로 처음부터 다시하기"):
        st.session_state.word_list = []
        st.session_state.current_index = 0
        st.rerun()
