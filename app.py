import streamlit as st
import random
from openai import OpenAI
from gtts import gTTS
import base64
import os

st.set_page_config(page_title="아이 영어 단어장", layout="centered")

st.title("🔤 단어 암기 퀴즈")

# Secrets에서 API 키 가져오기
api_key = st.secrets.get("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

st.write("#### 📸 단어장 사진 준비하기")

# 스마트폰용 한글 입력 선택 버튼
tab1, tab2 = st.tabs(["📷 바로 사진 찍기", "📁 앨범에서 가져오기"])

uploaded_file = None

with tab1:
    camera_file = st.camera_input("카메라로 단어장을 찍어주세요")
    if camera_file:
        uploaded_file = camera_file

with tab2:
    gallery_file = st.file_uploader("갤러리/파일에서 선택하세요", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if gallery_file:
        uploaded_file = gallery_file

# 단어 추출 진행
if uploaded_file and api_key and not st.session_state.word_list:
    if st.button("✨ 단어 공부 시작하기", type="primary", use_container_width=True):
        client = OpenAI(api_key=api_key)
        
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        with st.spinner("단어를 분석하고 있어요..."):
            try:
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
                
                # 순서 무작위 섞기
                random.shuffle(lines)
                st.session_state.word_list = lines
                st.session_state.current_index = 0
                st.rerun()
            except Exception as e:
                st.error("사진을 읽는 중 문제가 발생했습니다. 다시 시도해 주세요.")

# 단어 테스트 진행
if st.session_state.word_list:
    st.divider()
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.write(f"### 🎧 단어 ({idx + 1} / {total})")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 음성 생성 (천천히 발음)
    tts = gTTS(text=eng_word, lang='en', slow=True)
    tts.save("temp.mp3")
    
    audio_file = open("temp.mp3", "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    
    st.divider()
    
    # 정답 확인
    if st.checkbox("👁️ 스펠링 & 뜻 확인하기"):
        st.success(f"### {current_pair}")
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전 단어", use_container_width=True) and idx > 0:
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if st.button("다음 단어 ➡️", use_container_width=True) and idx < total - 1:
            st.session_state.current_index += 1
            st.rerun()
            
    st.write("")
    if st.button("🔄 다른 사진으로 새로 하기", use_container_width=True):
        st.session_state.word_list = []
        st.session_state.current_index = 0
        st.rerun()
