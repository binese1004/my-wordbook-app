import streamlit as st
import random
import google.generativeai as genai
from gtts import gTTS
import io
from PIL import Image, ImageOps

st.set_page_config(page_title="단어 암기 퀴즈", layout="centered")

st.title("🔤 단어 암기 퀴즈 (무료)")

# 1. API Key 불러오기 및 초기화
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

if not gemini_key:
    gemini_key = st.text_input("🔑 Google Gemini API Key를 입력해주세요", type="password")

if gemini_key:
    genai.configure(api_key=gemini_key.strip())

# 세션 상태 변수 초기화
if "raw_word_list" not in st.session_state:
    st.session_state.raw_word_list = []
if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "mode_selected" not in st.session_state:
    st.session_state.mode_selected = False
if "upload_type" not in st.session_state:
    st.session_state.upload_type = None

@st.cache_data
def process_image(file_data):
    image = Image.open(file_data)
    image = ImageOps.exif_transpose(image)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.thumbnail((1024, 1024))
    return image

# 2. 단어 추출 단계 (간결한 입력 버튼 UI)
if not st.session_state.raw_word_list:
    st.write("### 사진을 선택해 주세요")
    
    col_cam, col_file = st.columns(2)
    
    with col_cam:
        if st.button("📸 카메라로 촬영", use_container_width=True):
            st.session_state.upload_type = "camera"
            st.rerun()
            
    with col_file:
        if st.button("📁 앨범에서 선택", use_container_width=True):
            st.session_state.upload_type = "file"
            st.rerun()

    target_photo = None

    # 후면 카메라 우선 업로드 지원
    if st.session_state.upload_type == "camera":
        target_photo = st.file_uploader("📸 후면 카메라로 찍기", type=["jpg", "png", "jpeg"], accept_multiple_files=False, key="back_camera")
    elif st.session_state.upload_type == "file":
        target_photo = st.file_uploader("📁 앨범에서 선택", type=["jpg", "png", "jpeg"], accept_multiple_files=False, key="album_file")

    if target_photo:
        if not gemini_key:
            st.error("❌ Gemini API Key가 입력되지 않았습니다.")
        else:
            with st.spinner("⚡ 초고속 AI가 단어를 읽는 중입니다..."):
                try:
                    img = process_image(target_photo)
                    model = genai.GenerativeModel('gemini-3.6-flash')

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
                        st.session_state.raw_word_list = lines
                        st.session_state.mode_selected = False
                        st.rerun()
                    else:
                        st.error("글자를 인식하지 못했습니다. 단어가 선명하게 찍히도록 다시 시도해 주세요.")
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "Quota exceeded" in err_msg:
                        st.warning("⏳ 무료 사용량 제한에 도달했습니다. 약 30초~1분 후 다시 시도해 주세요!")
                    else:
                        st.error(f"오류 상세 내용: {err_msg}")

# 3. 재생 방식 선택 화면
elif st.session_state.raw_word_list and not st.session_state.mode_selected:
    total_count = len(st.session_state.raw_word_list)
    st.markdown("---")
    st.subheader(f"🎯 총 {total_count}개의 단어를 찾았습니다!")
    st.write("학습하실 방식을 선택해 주세요.")

    col1, col2, col3 = st.columns(3)

    # 방식 1: 순서대로
    with col1:
        if st.button("1️⃣ 순서대로", use_container_width=True):
            st.session_state.word_list = list(st.session_state.raw_word_list)
            st.session_state.current_index = 0
            st.session_state.mode_selected = True
            st.rerun()

    # 방식 2: 전체 섞기
    with col2:
        if st.button("2️⃣ 전체 섞기", use_container_width=True):
            shuffled = list(st.session_state.raw_word_list)
            random.shuffle(shuffled)
            st.session_state.word_list = shuffled
            st.session_state.current_index = 0
            st.session_state.mode_selected = True
            st.rerun()

    # 방식 3: 구간 섞기
    st.write("")
    st.markdown("---")
    st.write("**3️⃣ 특정 구간만 섞기 (예: 1번~7번)**")
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_num = st.number_input("시작 번호", min_value=1, max_value=total_count, value=1)
    with col_end:
        end_num = st.number_input("끝 번호", min_value=1, max_value=total_count, value=min(7, total_count))

    if st.button("🔀 구간 섞어서 시작하기", use_container_width=True):
        if start_num > end_num:
            st.error("시작 번호가 끝 번호보다 클 수 없습니다.")
        else:
            sub_list = list(st.session_state.raw_word_list[start_num - 1 : end_num])
            random.shuffle(sub_list)
            st.session_state.word_list = sub_list
            st.session_state.current_index = 0
            st.session_state.mode_selected = True
            st.rerun()

# 4. 단어 학습 및 음성 퀴즈 화면
elif st.session_state.mode_selected:
    total = len(st.session_state.word_list)
    idx = st.session_state.current_index
    
    st.markdown("---")
    st.subheader(f"🎧 단어 퀴즈 ({idx + 1} / {total})")
    
    current_pair = st.session_state.word_list[idx]
    eng_word = current_pair.split(':')[0].strip() if ':' in current_pair else current_pair
    
    # 음성 재생
    fp = io.BytesIO()
    tts = gTTS(text=eng_word, lang='en', slow=True)
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format="audio/mp3", autoplay=True)
    
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
    col_mode, col_reset = st.columns(2)
    with col_mode:
        if st.button("🔄 학습 방식 다시 선택", use_container_width=True):
            st.session_state.mode_selected = False
            st.rerun()
    with col_reset:
        if st.button("📸 다른 사진 찍기", use_container_width=True):
            st.session_state.raw_word_list = []
            st.session_state.word_list = []
            st.session_state.current_index = 0
            st.session_state.mode_selected = False
            st.session_state.upload_type = None
            st.rerun()
