from pypdf import PdfReader


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    full_text = ""
    page_count = len(reader.pages)

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    return {
        "text": full_text,
        "pages": page_count,
        "characters": len(full_text)
    }