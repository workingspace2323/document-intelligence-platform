import fitz  # PyMuPDF


def highlight_pdf(pdf_path, query):
    doc = fitz.open(pdf_path)

    for page in doc:

        text_instances = page.search_for(query)

        for inst in text_instances:
            highlight = page.add_highlight_annot(inst)
            highlight.update()

    output_path = "uploads/highlighted_output.pdf"
    doc.save(output_path)

    return output_path