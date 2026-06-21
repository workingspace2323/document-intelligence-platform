from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def create_vector_store(chunks):
    # Extract only text for embeddings
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(texts)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings).astype("float32"))

    # IMPORTANT: keep original chunks (with page info)
    return index, chunks


def search_chunks(question, index, chunks, top_k=5):

    question_embedding = model.encode([question])

    distances, indices = index.search(
        np.array(question_embedding).astype("float32"),
        top_k
    )

    results = []

    for idx in indices[0]:
        if idx < len(chunks):
            results.append(chunks[idx])

    return results
def search_chunks(
        question,
        index,
        chunks,
        top_k=5
):

    question_embedding = model.encode(
        [question]
    )

    distances, indices = index.search(
        np.array(question_embedding).astype("float32"),
        top_k
    )

    results = []

    for idx in indices[0]:
        results.append(chunks[idx])

    return results