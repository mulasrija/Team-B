import streamlit as st
import PyPDF2
from docx import Document
import requests
from datetime import datetime

st.set_page_config(page_title="Interview Prep Quiz", layout="wide")

# ---------- SESSION STATE ----------
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "question_count" not in st.session_state:
    st.session_state.question_count = 5

# ---------- HISTORY ----------
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "saved" not in st.session_state:
    st.session_state.saved = False


def start_new_quiz():
    """Reset current quiz progress and return to quiz creation view."""
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.user_answers = []
    st.session_state.quiz_started = False
    st.session_state.current_quiz = None
    st.session_state.saved = False


def delete_current_quiz():
    """Delete the selected quiz from history and adjust selection."""
    idx = st.session_state.get("current_quiz")
    if idx is None:
        return
    if 0 <= idx < len(st.session_state.quiz_history):
        st.session_state.quiz_history.pop(idx)

    if len(st.session_state.quiz_history) == 0:
        st.session_state.current_quiz = None
    else:
        st.session_state.current_quiz = max(0, idx - 1)


st.title("🧠 Interview Quiz Mode")
left, separator, right = st.columns([2, 0.08, 7])

with separator:
    st.markdown(
        "<div style='height:80vh;border-left:2px solid #e2e8f0;margin-left:8px;'></div>",
        unsafe_allow_html=True,
    )

with left:
    if st.button("➕ New Quiz", use_container_width=True, on_click=start_new_quiz):
        st.rerun()

    st.markdown(
        "<h3 style='margin:0; white-space:nowrap;'>📚 Quiz History</h3>",
        unsafe_allow_html=True,
    )
    st.divider()

    if len(st.session_state.quiz_history) == 0:
        st.info("📭 No quizzes yet")
    else:
        for index, chat in enumerate(st.session_state.quiz_history):
            title = chat["title"]

            if st.button(f"📄 {title}", key=f"hist_{index}", use_container_width=True):
                st.session_state.current_quiz = index

        st.divider()
        if st.session_state.current_quiz is not None:
            if st.button("🗑️ Delete Current Quiz", use_container_width=True, on_click=delete_current_quiz):
                st.rerun()


with right:
    # ---------- FILE UPLOAD ----------
    file = st.file_uploader("Upload PDF / DOCX / TXT", type=["pdf", "docx", "txt"])
    question_count = st.number_input(
        "Number of Questions",
        min_value=3,
        max_value=25,
        value=st.session_state.question_count,
        step=1,
        help="Choose how many MCQs to generate dynamically.",
    )
    st.session_state.question_count = int(question_count)

    def extract_text(file):
        if file.name.endswith(".pdf"):
            pdf = PyPDF2.PdfReader(file)
            return "".join([p.extract_text() or "" for p in pdf.pages])
        elif file.name.endswith(".docx"):
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif file.name.endswith(".txt"):
            return file.read().decode("utf-8")
        return ""

    # ---------- GENERATE QUIZ ----------
    if file and not st.session_state.quiz_started:
        text = extract_text(file)

        if st.button("Generate Quiz"):
            with st.spinner("Generating questions..."):

                prompt = f"""
    Generate {st.session_state.question_count} MCQs from the content below.

    Format STRICTLY like this:
    Q1: question
    A) option
    B) option
    C) option
    D) option
    Answer: A
    Explanation: explanation

    Content:
    {text[:3000]}
    """

                try:
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={"model": "mistral", "prompt": prompt, "stream": False}
                    )

                    data = response.json()["response"]
                    
                    if response.status_code != 200:
                        st.error("Ollama API failed")
                        st.write(response.text)
                        st.stop()

                    # ---------- PARSE ----------
                    blocks = data.split("\nQ")  # keep first Q intact
                    questions = []

                    for b in blocks:
                        b = b.strip()
                        if not b:
                            continue
                        # Add back Q if missing
                        if not b.startswith("Q"):
                            b = "Q" + b
                        lines = b.split("\n")
                        q_text = lines[0].split(":", 1)[1].strip() if ":" in lines[0] else lines[0].strip()
                        options = [l.strip() for l in lines if l.strip().startswith(("A)", "B)", "C)", "D)"))]
                        answer_line = next((l for l in lines if "Answer:" in l or "answer:" in l), "")
                        explanation_line = next((l for l in lines if "Explanation:" in l or "explanation:" in l), "")
                        if options and answer_line:
                            questions.append({
                                "question": q_text,
                                "options": options,
                                "answer": answer_line.split(":")[1].strip(),
                                "explanation": explanation_line.split(":",1)[1].strip() if explanation_line else ""
                            })

                    if not questions:
                        st.error("❌ No questions were generated. Check API response or file content.")
                        st.stop()

                    # Keep the exact number requested when model returns extras.
                    questions = questions[: st.session_state.question_count]

                    if len(questions) < st.session_state.question_count:
                        st.warning(
                            f"Only {len(questions)} questions were generated out of requested {st.session_state.question_count}."
                        )

                    st.session_state.questions = questions
                    st.session_state.quiz_started = True
                    st.rerun()

                except Exception as e:
                    st.error("⚠️ Error connecting to Ollama")
                    st.write(e)

    # ---------- QUIZ UI ----------
    if st.session_state.quiz_started and st.session_state.current_quiz is None:

        q_index = st.session_state.current_q
        questions = st.session_state.questions

        if q_index < len(questions):
            q = questions[q_index]

            st.subheader(f"Question {q_index + 1}")
            st.write(q["question"])

            # 🔥 NO DEFAULT SELECTION
            selected = st.radio(
                "Choose answer",
                ["-- Select an option --"] + q["options"],
                index=0,
                key=f"q_{q_index}"
            )

            if st.button("Next"):
                if selected == "-- Select an option --":
                    st.warning("Please select an answer")
                else:
                    st.session_state.user_answers.append(selected[0])

                    if selected[0] == q["answer"]:
                        st.session_state.score += 1

                    st.session_state.current_q += 1
                    st.rerun()

        else:
            # ---------- RESULT ----------
            st.success(f"🎉 Quiz Completed! Score: {st.session_state.score}/{len(questions)}")

            st.markdown("### 📘 Answers & Explanations")

            for i, q in enumerate(questions):
                st.write(f"**Q{i+1}: {q['question']}**")
                st.write(f"Correct Answer: {q['answer']}")
                st.write(q["explanation"])
                st.write("---")

            # ---------- SAVE HISTORY ----------
            quiz_data = {
                "title": f"{file.name} ({datetime.now().strftime('%H:%M')})",
                "questions": questions,
                "score": st.session_state.score,
                "total": len(questions),
            }

            if "saved" not in st.session_state:
                st.session_state.saved = False

            if not st.session_state.saved:
                st.session_state.quiz_history.append(quiz_data)
                st.session_state.saved = True

    # ---------- SHOW SELECTED HISTORY ----------
    if st.session_state.current_quiz is not None:
        ch = st.session_state.quiz_history[st.session_state.current_quiz]

        st.divider()
        st.markdown(f"### 📋 {ch['title']}")
        st.write(f"Score: {ch['score']}/{ch['total']}")

        st.markdown("### 📘 Answers & Explanations")

        for i, q in enumerate(ch["questions"]):
            st.write(f"**Q{i+1}: {q['question']}**")
            st.write(f"Correct Answer: {q['answer']}")
            st.write(q["explanation"])
            st.write("---")
