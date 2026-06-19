import streamlit as st
import os

from pdf_reader import extract_pdf_text
from gemini_client import ask_gemini

st.set_page_config(
    page_title="Document Intelligence Platform",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Document Intelligence Platform")

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file:

    save_path = os.path.join("uploads", uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdf_data = extract_pdf_text(save_path)

    st.success("PDF uploaded successfully!")

    st.write(f"📚 Pages: {pdf_data['pages']}")
    st.write(f"🔤 Characters: {pdf_data['characters']}")

    question = st.text_input(
        "Ask a question about the document"
    )

    if question:

        with st.spinner("Thinking..."):

            prompt = f"""
            You must answer only from the document below.

            DOCUMENT:
            {pdf_data['text'][:30000]}

            QUESTION:
            {question}

            If the answer is not present, say:
            'Information not found in document.'
            """

            answer = ask_gemini(prompt)

        st.subheader("Answer")
        st.write(answer)