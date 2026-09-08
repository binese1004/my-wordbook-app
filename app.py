import streamlit as st
import random
from openai import OpenAI
from gtts import gTTS
import base64
import io
from PIL import Image, ImageOps

st.set_page_config(page_title="단어 암기 퀴즈", layout="centered")

st.title("🔤 단어 암기 퀴즈")

# OpenAI API Key 설정
api_key = st.secrets.get("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API Key 입력", type="password")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# 이미지 회전 보정 및 Base64 변환 함수
def process_image(file_data):
    # 이미지 열기
    image = Image.open(file_data)
    
    # EXIF 방향 정보에 맞춰 이미지 자동 회전 (세로 사진 누움 방지)
    image = ImageOps.exif_transpose(image)
    
    # RGB 변환 (PNG/RGBA 대응)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    # 바이트 스트림으로 저장 후 Base64 인코딩 (ASCII 오류 방지)
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=95)
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

# 1. 단어 목록이 없을 때만 업로드 화면 표시
if not st.session_state.word_list:
    st.write("### 사진을 보내주세요")
    
    camera_photo = st.file_uploader(
        "📸 카메라로 바로 찍기", 
        type=["jpg", "png", "jpeg"],
        key="cam_input"
    )
    
    file_photo = st.file_uploader(
        "📁 앨범에서 선택하기", 
        type=["jpg", "png", "jpeg"],
        key="file_input"
    )

    target_photo = camera_photo or file_photo

    # 사진이 들어오면 자동으로 처리 시작
    if target_photo and api_key:
        with st.spinner("⚡ 사진 방향을 맞추고 단어를 읽고 있습니다..."):
            try:
                base64_image = process_image(target_photo)
                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": (
                                        "이 사진 속 영어 단어와 한글 뜻을 추출해줘. "
                                        "손글씨나 흐릿한 글자도 최대한 읽어서 '영어단어: 한글뜻' 형태로 한 줄에 하나씩만 작성해줘. "
                                        "다른 설명이나 인삿말은 전부 제외해."
                                    )
                                },
                                {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                raw_text = response.choices[0].message.content.strip()
                lines = [line.strip().replace("`", "") for line in raw_text.split('\n') if line.strip() and ":" in line]

                if lines:
                    random.shuffle(lines)  # 무작위 섞기
                    st.session_state.word_list = lines
                    st.session_state.current_index = 0
                    st.rerun()
                else:
                    st.error("글자를 인식하지 못했습니다. 단어장 사진을 다시 찍어주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")

# 2. 단어 음성 학습 화면
if st.session_state.word_list:
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.markdown("---")
    st.subheader(f"🎧 단어 퀴즈 ({idx + 1} / {total})")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 원어민 음성 생성 및 자동 재생
    tts = gTTS(text=eng_word, lang='en', slow=True)
    tts.save("temp.mp3")
    
    with open("temp.mp3", "rb") as f:
        audio_bytes = f.read()
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    
    st.write("")
    
    if st.checkbox("👁️ 정답(스펠링 & 뜻) 보기"):
        st.success(f"### {current_pair}")
        
    st.write("")
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 이전 단어", use_container_width=True) and idx > 0:
            st.session_state.current_index -= 1
            st.rerun()
    with col_next:
        if st.button("다음 단어 ➡️", use_container_width=True) and idx < total - 1:
            st.session_state.current_index += 1
            st.rerun()
            
    st.write("")
    st.markdown("---")
    if st.button("📸 다른 사진으로 다시 찍기", use_container_width=True):
        st.session_state.word_list = []
        st.session_state.current_index = 0
        st.rerun()
