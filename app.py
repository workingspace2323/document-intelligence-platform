import streamlit as st
import os
import uuid
import fitz
from PIL import Image

from document_reader import extract_file
from chunker import chunk_text
from vector_store import create_vector_store, search_chunks
from gemini_client import ask_gemini

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Document Workspace",
    page_icon="📄",
    layout="wide"
)

# ---------------- UI ---------------- #

st.markdown("""
<style>

.stApp {
    background: #f7f8fc;
    font-family: Inter;
}

[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e5e7eb;
}

div[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 10px;
}

.stButton > button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
}

.stButton > button:hover {
    background: #1d4ed8;
}

</style>
""", unsafe_allow_html=True)

# ---------------- STORAGE ---------------- #

BASE_DIR = "uploads"
os.makedirs(BASE_DIR, exist_ok=True)

# ---------------- MULTI USER ---------------- #

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

USER_DIR = os.path.join(BASE_DIR, st.session_state.user_id)
os.makedirs(USER_DIR, exist_ok=True)

# ---------------- SESSION STATE ---------------- #

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "current_doc" not in st.session_state:
    st.session_state.current_doc = None

if "chat" not in st.session_state:
    st.session_state.chat = {}

# ---------------- PDF PAGE RENDER ---------------- #

def render_pdf_page(file_path, page_number):

    doc = fitz.open(file_path)

    if page_number < 0 or page_number >= len(doc):
        return None

    page = doc[page_number]

    pix = page.get_pixmap(
        matrix=fitz.Matrix(1.5, 1.5)
    )

    img = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    return img

# ---------------- FILE LIST ---------------- #

def get_docs():

    allowed = ["pdf", "docx", "txt", "xlsx", "xls", "pptx"]

    files = []

    for f in os.listdir(USER_DIR):

        path = os.path.join(USER_DIR, f)

        if not os.path.isfile(path):
            continue

        if "." not in f:
            continue

        ext = f.split(".")[-1].lower()

        if ext in allowed:
            files.append(f)

    return files

# ---------------- SIDEBAR ---------------- #

with st.sidebar:

    st.title("📄 My Documents")

    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt", "xlsx", "xls", "pptx"]
    )

    docs = get_docs()

    selected_doc = st.selectbox(
        "Select Document",
        docs
    ) if docs else None

    col1, col2 = st.columns(2)

    open_btn = col1.button("Open")
    delete_btn = col2.button("Delete")

    st.markdown("---")

    summary_btn = st.button("📋 Summary")
    brief_btn = st.button("📊 Executive Brief")

# ---------------- UPLOAD ---------------- #

if uploaded_file:

    file_path = os.path.join(
        USER_DIR,
        uploaded_file.name
    )

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    data = extract_file(file_path)

    chunks = chunk_text(
        data["pages_data"],
        800
    )

    index, stored = create_vector_store(chunks)

    st.session_state.index = index
    st.session_state.chunks = stored
    st.session_state.current_doc = uploaded_file.name

    st.session_state.chat.setdefault(
        uploaded_file.name,
        []
    )

    st.success("Uploaded securely")

# ---------------- OPEN ---------------- #

if open_btn and selected_doc:

    file_path = os.path.join(
        USER_DIR,
        selected_doc
    )

    data = extract_file(file_path)

    chunks = chunk_text(
        data["pages_data"],
        800
    )

    index, stored = create_vector_store(chunks)

    st.session_state.index = index
    st.session_state.chunks = stored
    st.session_state.current_doc = selected_doc

    st.session_state.chat.setdefault(
        selected_doc,
        []
    )

    st.success(f"{selected_doc} loaded")

# ---------------- DELETE ---------------- #

if delete_btn and selected_doc:

    file_path = os.path.join(
        USER_DIR,
        selected_doc
    )

    try:
        os.remove(file_path)
    except:
        pass

    st.session_state.chat.pop(
        selected_doc,
        None
    )

    if st.session_state.current_doc == selected_doc:

        st.session_state.index = None
        st.session_state.chunks = None
        st.session_state.current_doc = None

    st.rerun()

# ---------------- HEADER ---------------- #

st.title("📄 Document Workspace")

if st.session_state.current_doc:

    st.info(
        f"User: {st.session_state.user_id[:8]} | Active: {st.session_state.current_doc}"
    )

# ---------------- LAYOUT ---------------- #

col1, col2 = st.columns([1.3, 1])

# ---------------- CHAT ---------------- #

with col1:

    doc = st.session_state.current_doc

    chat = st.session_state.chat.get(
        doc,
        []
    )

    for msg in chat:

        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input(
        "Ask anything from your document..."
    )

    if question:

        if st.session_state.index is None:

            st.warning(
                "Open a document first"
            )

            st.stop()

        chat.append({
            "role": "user",
            "content": question
        })

        results = search_chunks(
            question,
            st.session_state.index,
            st.session_state.chunks,
            top_k=5
        )

        context = "\n".join(
            [
                f"PAGE {c['page']}:\n{c['text']}"
                for c in results
            ]
        )

        prompt = f"""
You are a document AI assistant.

Use ONLY the supplied context.

If the answer is not found,
reply exactly:

Not found in document.

Context:
{context}

Question:
{question}
"""

        answer = ask_gemini(prompt)

        chat.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant"):
            st.write(answer)

# ---------------- PDF VIEWER ---------------- #

with col2:

    st.subheader("📄 PDF Viewer")

    if st.session_state.current_doc:

        file_path = os.path.join(
            USER_DIR,
            st.session_state.current_doc
        )

        if file_path.lower().endswith(".pdf"):

            try:

                doc = fitz.open(file_path)

                total_pages = len(doc)

                page_no = st.slider(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )

                image = render_pdf_page(
                    file_path,
                    page_no - 1
                )

                if image:

                    st.image(
                        image,
                        width=700
                    )

            except Exception as e:

                st.error(
                    f"PDF Viewer Error: {e}"
                )

        else:

            st.info(
                "PDF viewer available only for PDF files."
            )

    else:

        st.info("No document loaded")

# ---------------- SUMMARY ---------------- #

if summary_btn and st.session_state.index:

    full = "\n".join(
        [
            f"PAGE {c['page']}:\n{c['text']}"
            for c in st.session_state.chunks
        ]
    )

    st.subheader("📋 Summary")

    prompt = f"""
Create a structured summary:

- Purpose
- Findings
- Risks
- Conclusion

Context:
{full}
"""

    st.write(
        ask_gemini(prompt)
    )

# ---------------- EXECUTIVE BRIEF ---------------- #

if brief_btn and st.session_state.index:

    full = "\n".join(
        [
            f"PAGE {c['page']}:\n{c['text']}"
            for c in st.session_state.chunks
        ]
    )

    st.subheader("📊 Executive Brief")

    prompt = f"""
Create an executive brief:

- Summary
- Insights
- Risks
- Recommendations

Context:
{full}
"""

    st.write(
        ask_gemini(prompt)
    )