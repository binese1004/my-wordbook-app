import streamlit as st
import random
from openai import OpenAI
from gtts import gTTS
import base64

st.set_page_config(page_title="아이 영어 단어장", layout="centered")

st.title("🔤 단어 암기 퀴즈")

# Secrets에서 API 키 가져오기
api_key = st.secrets.get("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

if "word_list" not in st.session_state:
    st.session_state.word_list = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

st.write("#### 📸 단어장 사진 준비하기")
st.info("💡 선명한 인식을 위해 **스마트폰 기본 카메라로 사진을 먼저 찍은 뒤 '앨범에서 사진 선택하기'**로 업로드하시는 것을 추천합니다.")

captured_file = st.camera_input("카메라로 단어장 찍기")
uploaded_file = st.file_uploader("또는 앨범에서 사진 선택하기", type=["jpg", "png", "jpeg"])

target_file = captured_file or uploaded_file

# 단어 추출 진행
if target_file and api_key and not st.session_state.word_list:
    if st.button("✨ 단어 공부 시작하기", type="primary", use_container_width=True):
        client = OpenAI(api_key=api_key)
        
        bytes_data = target_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        with st.spinner("단어를 분석하고 있어요... (시간이 조금 걸릴 수 있습니다)"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": (
                                        "사진 속에 있는 영어 단어와 그에 해당하는 한글 뜻을 찾아주세요. "
                                        "손글씨나 흐릿한 글자도 맥락에 맞게 유추해서 읽어주세요. "
                                        "출력 형식은 오직 '영어단어: 한글뜻' 형태로만 한 줄에 하나씩 작성해주세요. "
                                        "다른 인삿말, 설명, 마크다운(```)은 절대로 포함하지 마세요."
                                    )
                                },
                                {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "high"  # 선명한 인식을 위해 high 고해상도 설정
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                raw_text = response.choices[0].message.content.strip()
                
                # 마크다운이나 불필요한 공백 제거
                lines = [line.strip().replace("`", "") for line in raw_text.split('\n') if line.strip() and ":" in line]
                
                if not lines:
                    # 콜론(:)이 없는 경우 처리
                    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

                if lines:
                    random.shuffle(lines)
                    st.session_state.word_list = lines
                    st.session_state.current_index = 0
                    st.rerun()
                else:
                    st.warning("사진에서 단어를 찾지 못했습니다. 글자가 더 선명하게 보이도록 다시 찍어주세요.")
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

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
