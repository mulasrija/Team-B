import streamlit as st
from datetime import datetime
import requests
import PyPDF2
from docx import Document
import tempfile
import os
from ocrfile import extract_text_from_image, extract_text_from_scanned_pdf



# ---------- RESUME EXTRACTION FUNCTIONS ----------
def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def extract_text_from_docx(file):
    """Extract text from DOCX file"""
    try:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"


def extract_text_from_txt(file):
    """Extract text from TXT file"""
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"Error reading TXT: {str(e)}"


def extract_resume_content(resume_file):
    """Extract content from resume based on file type"""
    
    if resume_file is None:
        return ""
    
    file_extension = resume_file.name.split(".")[-1].lower()

    try:
        # -------- PDF --------
        if file_extension == "pdf":
            # Try normal PDF extraction first
            text = extract_text_from_pdf(resume_file)

            # If empty, assume scanned PDF → use OCR
            if not text or text.strip() == "":
                resume_file.seek(0)  # Reset file pointer
                return extract_text_from_scanned_pdf(resume_file)
            
            return text

        # -------- DOCX --------
        elif file_extension == "docx":
            return extract_text_from_docx(resume_file)

        # -------- TXT --------
        elif file_extension == "txt":
            return extract_text_from_txt(resume_file)

        # -------- IMAGE FILES --------
        elif file_extension in ["png", "jpg", "jpeg"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
                tmp.write(resume_file.read())
                temp_path = tmp.name

            return extract_text_from_image(temp_path)

        else:
            return "Unsupported file format"

    except Exception as e:
        return f"Error extracting resume: {str(e)}"



# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Cover Letter Chatbot", layout="wide")

# ---------- CUSTOM CSS FOR LIGHT COLORS ----------

# Centered header with logo and title on same line
left_col, center_col, right_col = st.columns([1, 3, 1])
with center_col:
    logo_col, title_col = st.columns([0.5, 4])
    with logo_col:
        st.image("data:image/png;base64,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", width=80)
    with title_col:
        st.title("AI Cover Letter Generator Chatbot")
# ---------- SESSION STATE INITIALIZATION ----------
if "history" not in st.session_state:
    st.session_state.history = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


def _delete_current_chat():
    # safe-delete current chat and trigger UI refresh
    idx = st.session_state.get("current_chat")
    if idx is None:
        return
    if 0 <= idx < len(st.session_state.history):
        st.session_state.history.pop(idx)
    # adjust current_chat
    if len(st.session_state.history) == 0:
        st.session_state.current_chat = None
    else:
        st.session_state.current_chat = max(0, idx - 1)
    try:
        st.experimental_rerun()
    except Exception:
        pass

# initialize input fields in session state so they can be cleared/reset
if "name" not in st.session_state:
    st.session_state.name = ""
if "company" not in st.session_state:
    st.session_state.company = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
# Use a changing key for the file_uploader so we can "clear" it by bumping the key
if "resume_uploader_key" not in st.session_state:
    st.session_state.resume_uploader_key = 0
if "show_success" not in st.session_state:
    st.session_state.show_success = False
if "resume_text_cache" not in st.session_state:
    st.session_state.resume_text_cache = None


# ---------- PAGE LAYOUT (20% LEFT - 80% RIGHT) ----------
left, separator, right = st.columns([2, 0.08, 7])

# vertical separator between history and main content
with separator:
    st.markdown(
        "<div style='height:80vh;border-left:2px solid #e2e8f0;margin-left:8px;'></div>",
        unsafe_allow_html=True,
    )


# ================= LEFT SIDE - CHAT HISTORY =================
with left:
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.current_chat = None
            st.session_state.name = ""
            st.session_state.company = ""
            st.session_state.role = ""
            st.session_state.job_description = ""
            st.session_state.resume_uploader_key += 1
    
    st.subheader("💬 Chat History")
    st.divider()

    if len(st.session_state.history) == 0:
        st.info("📭 No chats yet. Start a new conversation!")
    else:
        # Display chats as clickable buttons with styling
        for index, chat in enumerate(st.session_state.history):
            title = chat.get("title", f"Chat {index+1}")
            if st.button(f"📄 {title}", key=f"chat_{index}", use_container_width=True):
                st.session_state.current_chat = index

        st.divider()

        if st.session_state.current_chat is not None:
            st.button("🗑️ Delete Current Chat", use_container_width=True, on_click=_delete_current_chat)
    
    st.markdown('</div>', unsafe_allow_html=True)


# ================= RIGHT SIDE - CHATBOT INPUT FORM =================
with right:
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Name", key="name", placeholder="your name")
    with col2:
        company = st.text_input("🏢 Company Name", key="company", placeholder="Google")
    
    col3, col4 = st.columns(2)
    with col3:
        role = st.text_input("💼 Role Name", key="role", placeholder="Senior Developer")
    with col4:
        st.write("📄 Upload Your Resume")
        resume_key = f"resume_{st.session_state.resume_uploader_key}"
        resume = st.file_uploader("Choose File", type=["pdf", "txt", "docx","png", "jpg", "jpeg"], key=resume_key, label_visibility="collapsed")

    # If a resume is uploaded, extract and show a quick preview
    resume_preview = ""
    if resume is not None:
        # Extract ONLY if not already cached
        if st.session_state.resume_text_cache is None:
            with st.spinner("Extracting resume text..."):
                try:
                    st.session_state.resume_text_cache = extract_resume_content(resume)
                except Exception as e:
                    st.session_state.resume_text_cache = f"Error extracting resume: {e}"

        resume_preview = st.session_state.resume_text_cache

    if resume is not None:
        with st.expander("Preview Extracted Resume", expanded=False):
            st.write(resume_preview if resume_preview else "No text extracted from this file.")

    job_description = st.text_area("📝 Job Description", key="job_description", placeholder="Paste the job description here...", height=120)

    st.divider()
    
    col_btn, col_spacer = st.columns([1, 2])
    with col_btn:
        generate = st.button("🚀 Generate Cover Letter", use_container_width=True, type="primary")

    # ---------- GENERATE BUTTON LOGIC ----------
    if generate:
        if name and company and role and job_description:
            with st.spinner("Generating cover letter..."):
                # Extract resume content if provided (use the preview if already extracted)
                resume_content = st.session_state.resume_text_cache or ""
                
                # Create AI prompt
                prompt = f"""
Act as an expert professional cover letter writer.

Using ONLY the data provided below, generate a highly personalized cover letter.

Replace every placeholder with real values.
Do NOT output any bracket text.
Do NOT output generic statements.
Make the letter specific to the company and job role.

Candidate Name: {name}
Company Name: {company}
Job Role: {role}

Job Description:
{job_description}

Resume Data:
{resume_content}

Return only the final formatted cover letter.
"""


                # Ollama API endpoint
                url = "http://localhost:11434/api/generate"

                data = {
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False
                }

                try:
                    response = requests.post(url, json=data)

                    if response.status_code == 200:
                        result = response.json()
                        cover_letter = result["response"]

                        # Remove everything before "Dear"
                        start_index = cover_letter.lower().find("dear")
                        if start_index != -1:
                            cover_letter = cover_letter[start_index:]

                        # Remove common unwanted lines
                        bad_phrases = [
                            "here is your cover letter",
                            "i will generate",
                            "please wait",
                            "hello",
                            "hi "
                        ]

                        for phrase in bad_phrases:
                            cover_letter = cover_letter.replace(phrase, "")

                        st.session_state.show_success = True
                    else:
                        st.error("Ollama Error")
                        st.write(response.text)
                        cover_letter = "Error generating cover letter."

                except Exception as e:
                    st.error("Ollama server not running!")
                    st.write(str(e))
                    cover_letter = "Ollama server not running."


            # Save chat history
            title = f"{company} - {role} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

            chat = {
                "title": title,
                "company": company,
                "role": role,
                "cover_letter": cover_letter,
                "resume": resume.name if resume is not None else None,
                "resume_content": resume_content,
                "timestamp": datetime.now().isoformat(),
            }

            st.session_state.history.append(chat)
            st.session_state.current_chat = len(st.session_state.history) - 1
            st.rerun()

        else:
            st.error("❌ Please fill all fields before generating")

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- DISPLAY SUCCESS MESSAGE ----------
    if st.session_state.show_success:
        st.success("✅ Cover Letter Generated Successfully!")
        st.session_state.show_success = False

    # ---------- DISPLAY SELECTED CHAT ----------
    if st.session_state.current_chat is not None and len(st.session_state.history) > 0:
        st.divider()
        ch = st.session_state.history[st.session_state.current_chat]

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**📋 {ch.get('title')}**")
        
        if ch.get("resume"):
            st.markdown(f"📎 Resume: {ch.get('resume')}")

        # Show extracted resume content if available
        # if ch.get("resume_content"):
        #     with st.expander("Extracted Resume Content", expanded=False):
        #         st.write(ch.get("resume_content"))

        st.markdown("**Generated Cover Letter:**")
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; border-left: 4px solid grey; padding: 20px; border-radius: 8px; line-height: 1.8; color: #1f2937; font-size: 16px;">
            {ch.get('cover_letter', '').replace(chr(10), '<br>')}
            </div>
            """,
            unsafe_allow_html=True
        )
