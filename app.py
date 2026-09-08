import streamlit as st
import random
import google.generativeai as genai
from gtts import gTTS
import io
from PIL import Image, ImageOps

st.set_page_config(page_title="단어 암기 퀴즈", layout="centered")

st.title("🔤 단어 암기 퀴즈 (무료)")

# 1. Secrets에서 API Key 불러오기
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

if not gemini_key or "여기에" in gemini_key:
    gemini_key = st.text_input("🔑 Google Gemini API Key를 입력해주세요", type="password")
    st.info("💡 API Key가 없으시면 https://aistudio.google.com/app/apikey 에서 무료로 발급받으실 수 있습니다.")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

def process_image(file_data):
    image = Image.open(file_data)
    image = ImageOps.exif_transpose(image)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return image

# 2. 단어 목록이 없을 때 업로드 화면
if not st.session_state.word_list:
    st.write("### 사진을 보내주세요")
    
    camera_photo = st.file_uploader("📸 카메라로 바로 찍기", type=["jpg", "png", "jpeg"], key="cam_input")
    file_photo = st.file_uploader("📁 앨범에서 선택하기", type=["jpg", "png", "jpeg"], key="file_input")

    target_photo = camera_photo or file_photo

    if target_photo:
        if not gemini_key:
            st.error("❌ Gemini API Key가 입력되지 않았습니다. Secrets 설정이나 상단 입력창을 확인해 주세요.")
        else:
            with st.spinner("⚡ 무료 AI가 사진속 단어를 읽고 있습니다..."):
                try:
                    img = process_image(target_photo)
                    
                    # Gemini API 설정
                    genai.configure(api_key=gemini_key.strip())
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    prompt_text = (
                        "이 사진 속 영어 단어와 한글 뜻을 추출해줘. "
                        "반드시 '영어단어: 한글뜻' 형태로 한 줄에 하나씩만 작성해줘. "
                        "예시: practice: 연습하다 "
                        "다른 설명, 인사말, 기호는 절대로 포함하지 마."
                    )
                    
                    response = model.generate_content([prompt_text, img])
                    
                    raw_text = response.text.strip()
                    lines = [line.strip().replace("`", "") for line in raw_text.split('\n') if line.strip() and ":" in line]

                    if lines:
                        random.shuffle(lines)
                        st.session_state.word_list = lines
                        st.session_state.current_index = 0
                        st.rerun()
                    else:
                        st.error("글자를 인식하지 못했습니다. 단어가 선명하게 찍히도록 다시 시도해 주세요.")
                except Exception as e:
                    st.error(f"오류 상세 내용: {str(e)}")

# 3. 단어 음성 학습 화면
if st.session_state.word_list:
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.markdown("---")
    st.subheader(f"🎧 단어 퀴즈 ({idx + 1} / {total})")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 음성 파일 생성
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
