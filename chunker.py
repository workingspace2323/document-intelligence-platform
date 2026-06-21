def chunk_text(pages_data, chunk_size=800):

    chunks = []

    for page_data in pages_data:

        page_number = page_data["page"]
        text = page_data["text"]

        for i in range(0, len(text), chunk_size):

            chunk = text[i:i + chunk_size]

            chunks.append({
                "page": page_number,
                "text": chunk
            })

    return chunks