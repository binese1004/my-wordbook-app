import streamlit as st
import random
from openai import OpenAI
from gtts import gTTS
import base64
import io
from PIL import Image, ImageOps

st.set_page_config(page_title="단어 암기 퀴즈", layout="centered")

st.title("🔤 단어 암기 퀴즈")

# API 키 가져오기
api_key = st.secrets.get("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API Key 입력", type="password")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

def process_image(file_data):
    # 이미지를 열고 회전 및 RGB 변환
    image = Image.open(file_data)
    image = ImageOps.exif_transpose(image)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# 1. 단어 목록이 없을 때 업로드 화면
if not st.session_state.word_list:
    st.write("### 사진을 보내주세요")
    
    camera_photo = st.file_uploader("📸 카메라로 바로 찍기", type=["jpg", "png", "jpeg"], key="cam_input")
    file_photo = st.file_uploader("📁 앨범에서 선택하기", type=["jpg", "png", "jpeg"], key="file_input")

    target_photo = camera_photo or file_photo

    if target_photo and api_key:
        with st.spinner("⚡ 사진을 분석하고 있습니다..."):
            try:
                base64_image = process_image(target_photo)
                client = OpenAI(api_key=api_key)

                # 단어 추출 요청
                prompt_text = "이 사진 속 영어 단어와 한글 뜻을 추출해줘. '영어단어: 한글뜻' 형태로 한 줄에 하나씩만 작성해줘. 다른 설명은 제외해."
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                
                raw_text = response.choices[0].message.content
                lines = [line.strip().replace("`", "") for line in raw_text.split('\n') if line.strip() and ":" in line]

                if lines:
                    random.shuffle(lines)
                    st.session_state.word_list = lines
                    st.session_state.current_index = 0
                    st.rerun()
                else:
                    st.error("글자를 인식하지 못했습니다. 단어장이 더 선명하게 보이도록 다시 찍어주세요.")
            except Exception as err:
                # ASCII 인코딩 에러 방지를 위한 안전한 문자열 처리
                safe_msg = str(err).encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                st.error(f"오류가 발생했습니다: {safe_msg}")

# 2. 단어 음성 학습 화면
if st.session_state.word_list:
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.markdown("---")
    st.subheader(f"🎧 단어 퀴즈 ({idx + 1} / {total})")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 음성 생성
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
