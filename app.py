import streamlit as st
import os
import uuid
import fitz
from PIL import Image

from document_reader import extract_file
from chunker import chunk_text
from vector_store import create_vector_store, search_chunks
from gemini_client import ask_gemini

# ---------------- CONFIG ---------------- #
st.set_page_config(
    page_title="Document AI Platform",
    page_icon="📄",
    layout="wide"
)

# ---------------- SESSION SAFE INIT ---------------- #
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

BASE_DIR = "uploads"
USER_DIR = os.path.join(BASE_DIR, st.session_state.user_id)
os.makedirs(USER_DIR, exist_ok=True)

if "chat" not in st.session_state:
    st.session_state.chat = {}

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "current_doc" not in st.session_state:
    st.session_state.current_doc = None

if "pdf_pages" not in st.session_state:
    st.session_state.pdf_pages = []

# ---------------- PDF RENDER (SAFE) ---------------- #
def render_pdf(path):
    doc = fitz.open(path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

# ---------------- FILE LIST ---------------- #
def list_files():
    if not os.path.exists(USER_DIR):
        return []
    return [f for f in os.listdir(USER_DIR) if f.endswith(".pdf")]

# ---------------- SIDEBAR ---------------- #
with st.sidebar:
    st.title("📁 Documents")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    files = list_files()
    selected = st.selectbox("Your Files", files) if files else None

    open_btn = st.button("Open")
    delete_btn = st.button("Delete")

# ---------------- UPLOAD ---------------- #
if file:
    path = os.path.join(USER_DIR, file.name)

    with open(path, "wb") as f:
        f.write(file.getbuffer())

    data = extract_file(path)
    chunks = chunk_text(data["pages_data"], 800)

    index, stored = create_vector_store(chunks)

    st.session_state.index = index
    st.session_state.chunks = stored
    st.session_state.current_doc = file.name
    st.session_state.chat[file.name] = []

    st.session_state.pdf_pages = render_pdf(path)

    st.success("Uploaded")

# ---------------- OPEN ---------------- #
if open_btn and selected:
    path = os.path.join(USER_DIR, selected)

    data = extract_file(path)
    chunks = chunk_text(data["pages_data"], 800)

    index, stored = create_vector_store(chunks)

    st.session_state.index = index
    st.session_state.chunks = stored
    st.session_state.current_doc = selected
    st.session_state.chat[selected] = []

    st.session_state.pdf_pages = render_pdf(path)

# ---------------- DELETE ---------------- #
if delete_btn and selected:
    try:
        os.remove(os.path.join(USER_DIR, selected))
    except:
        pass

    st.rerun()

# ---------------- UI ---------------- #
st.title("📄 Document AI Workspace")

col1, col2 = st.columns([1.3, 1])

# ---------------- CHAT ---------------- #
with col1:
    doc = st.session_state.current_doc

    chat = st.session_state.chat.get(doc, [])

    for msg in chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    q = st.chat_input("Ask your document")

    if q:
        if not st.session_state.index:
            st.warning("Open a document first")
            st.stop()

        chat.append({"role": "user", "content": q})

        results = search_chunks(q, st.session_state.index, st.session_state.chunks)

        context = "\n".join([r["text"] for r in results])

        prompt = f"""
Answer using only context.

Context:
{context}

Question:
{q}
"""

        ans = ask_gemini(prompt)

        chat.append({"role": "assistant", "content": ans})

        st.rerun()

# ---------------- PDF VIEWER ---------------- #
with col2:
    st.subheader("PDF Viewer")

    if st.session_state.pdf_pages:
        page = st.slider("Page", 1, len(st.session_state.pdf_pages), 1)
        st.image(st.session_state.pdf_pages[page - 1], use_container_width=True)
    else:
        st.info("Upload a PDF")