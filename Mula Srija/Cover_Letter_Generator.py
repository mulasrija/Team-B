import os

# 🔥 Fix Paddle 3.x issues
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import streamlit as st
from datetime import datetime
import requests
import PyPDF2
import docx
from paddleocr import PaddleOCR
import tempfile

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Career Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- DARK UI CSS ----------------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: linear-gradient(135deg, #0f172a, #111827) !important;
    min-height: 100vh;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] {
    background-color: #0b1120 !important;
}

section[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

h1 { color: #3b82f6 !important; }
h2, h3 { color: #60a5fa !important; }

.assistant-box {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 20px;
    border-radius: 12px;
    border-left: 4px solid #3b82f6;
    line-height: 1.8;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "mode" not in st.session_state:
    st.session_state.mode = "Cover Letter"

# ---------------- INIT OCR ----------------
@st.cache_resource
def load_ocr():
    return PaddleOCR(lang="en", use_textline_orientation=True)

ocr = load_ocr()

# ---------------- FILE TEXT EXTRACTION ----------------
def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()

    try:
        uploaded_file.seek(0)

        if file_type == "txt":
            return uploaded_file.read().decode("utf-8", errors="ignore")

        elif file_type == "pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
            return text

        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])

        elif file_type in ["jpg", "jpeg", "png"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            result = ocr.ocr(tmp_path)

            text = ""
            if result:
                for page in result:
                    for line in page:
                        if isinstance(line, list) and len(line) > 1:
                            text += line[1][0] + "\n"

            os.remove(tmp_path)
            return text

        return ""

    except Exception as e:
        return f"[Error reading {uploaded_file.name}: {str(e)}]"

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("💬 Chat History")

    # 🎯 Mode Selector
    st.session_state.mode = st.selectbox(
        "🎯 Select Mode",
        ["Cover Letter", "Interview Preparation"]
    )

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_chat = None
        st.rerun()

    st.divider()

    if len(st.session_state.history) == 0:
        st.info("No chats yet")
    else:
        for idx, chat in enumerate(st.session_state.history):
            if st.button(chat["title"], key=idx, use_container_width=True):
                st.session_state.current_chat = idx

# ---------------- MAIN ----------------
st.title("🚀 AI Career Assistant")

# ================= COVER LETTER MODE =================
if st.session_state.mode == "Cover Letter":

    st.header("📄 Cover Letter Generator")

    col1, col2 = st.columns(2)

    with col1:
        resume_file = st.file_uploader(
            "📘 Upload Resume",
            type=["pdf", "txt", "docx", "jpg", "jpeg", "png"]
        )

    with col2:
        job_file = st.file_uploader(
            "📑 Upload Job Description",
            type=["pdf", "txt", "docx", "jpg", "jpeg", "png"]
        )

    generate_btn = st.button("🚀 Generate Cover Letter", use_container_width=True)

    if generate_btn:

        if resume_file and job_file:

            with st.spinner("Generating cover letter..."):

                resume_text = extract_text_from_file(resume_file)
                job_text = extract_text_from_file(job_file)

                prompt = f"""
Write a professional, ATS-optimized cover letter.

Resume:
{resume_text}

Job Description:
{job_text}
"""

                try:
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "phi",
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=120
                    )

                    output = response.json().get("response", "")

                except Exception as e:
                    output = f"⚠️ Error: {str(e)}"

            title = f"Cover Letter - {datetime.now().strftime('%H:%M')}"

            st.session_state.history.append({
                "title": title,
                "content": output
            })

            st.session_state.current_chat = len(st.session_state.history) - 1

        else:
            st.error("Upload both files")

# ================= INTERVIEW MODE =================
elif st.session_state.mode == "Interview Preparation":

    st.header("🎯 Interview Preparation Assistant")

    study_files = st.file_uploader(
        "📚 Upload Study Materials",
        type=["pdf", "txt", "docx", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    analyze_btn = st.button("🧠 Generate Interview Prep", use_container_width=True)

    if analyze_btn:

        if study_files:

            with st.spinner("Processing study materials..."):

                combined_text = ""

                for file in study_files:
                    combined_text += extract_text_from_file(file) + "\n"

                prompt = f"""
You are an expert interview coach.

Material:
{combined_text}

Generate:
1. Summary
2. Important Questions
3. Answers
4. Key Concepts
"""

                try:
                    response = requests.post(
                        "http://host.docker.internal:11434/api/generate",
                        json={
                            "model": "phi",
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=180
                    )

                    output = response.json().get("response", "")

                except Exception as e:
                    output = f"⚠️ Error: {str(e)}"

            title = f"Interview Prep - {datetime.now().strftime('%H:%M')}"

            st.session_state.history.append({
                "title": title,
                "content": output
            })

            st.session_state.current_chat = len(st.session_state.history) - 1

        else:
            st.error("Upload at least one file")

# ---------------- DISPLAY ----------------
if st.session_state.current_chat is not None:

    st.divider()

    chat = st.session_state.history[st.session_state.current_chat]

    st.markdown(f"### 📋 {chat['title']}")

    st.markdown(
        f"""
        <div class="assistant-box">
        {chat['content'].replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.download_button(
        "⬇️ Download",
        data=chat["content"],
        file_name="output.txt",
        mime="text/plain",
        use_container_width=True
    )
