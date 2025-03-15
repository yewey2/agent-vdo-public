import faiss
import pickle
import numpy as np
import ast
from sentence_transformers import SentenceTransformer
import os

def loadTexts():
    # Load data from .txt file
    with open("groundtruths.txt", "r", encoding="utf-8") as f:
        raw_data = f.read()

    # Convert string to list of lists
    data = ast.literal_eval(raw_data)  # Safely parses Python-style lists

    # Extract texts, labels, and scores
    texts = [entry[0] for entry in data]
    labels = [entry[1] for entry in data]
    scores = [float(entry[2]) for entry in data]  # Convert scores to float
    return texts, labels, scores

def getIndexFromText(texts, saveIndex = True, index_file = "faiss_index.bin", mdl_name = "all-MiniLM-L6-v2"):
    # Check if FAISS index file exists
    if os.path.exists(index_file):
        print("Loading existing FAISS index...")
        index = faiss.read_index(index_file)  # Load existing index
        return index
    # Generate normalized embeddings
    model = SentenceTransformer(mdl_name)
    embeddings = model.encode(texts, normalize_embeddings=True)
    embeddings = np.array(embeddings).astype("float32")  # Convert to float32

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    if saveIndex == True:
        # Save FAISS index
        faiss.write_index(index, index_file)  

        # # Save metadata (labels and scores)
        # metadata = {"labels": labels, "scores": scores}
        # with open("metadata.pkl", "wb") as f:
        #     pickle.dump(metadata, f)

        print("FAISS index and metadata saved successfully!")
    return index

def getIndex(saveIndex = True, index_file = "faiss_index.bin"):
    # Check if FAISS index file exists
    if os.path.exists(index_file):
        print("Loading existing FAISS index...")
        index = faiss.read_index(index_file)  # Load existing index
        return index
    texts, labels, scores = loadTexts()
    # Load sentence transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate normalized embeddings
    embeddings = model.encode(texts, normalize_embeddings=True)
    embeddings = np.array(embeddings).astype("float32")  # Convert to float32

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    if saveIndex == True:
        # Save FAISS index
        faiss.write_index(index, index_file)  

        # # Save metadata (labels and scores)
        # metadata = {"labels": labels, "scores": scores}
        # with open("metadata.pkl", "wb") as f:
        #     pickle.dump(metadata, f)

        print("FAISS index and metadata saved successfully!")
    return index

def compareQueryIssues(index, query, k=10):
    # Load sentence transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Encode input
    query_embedding = model.encode([query], normalize_embeddings=True).astype("float32")

    # Search FAISS index for top 5 closest matches
    # k = 5  # Number of nearest neighbors
    distances, indices = index.search(query_embedding, k)
    indices = indices.flatten()
    return distances, indices.flatten()

def compareQuery(index, query, k=5):
    # Load sentence transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Encode input
    query_embedding = model.encode([query], normalize_embeddings=True).astype("float32")

    # Search FAISS index for top 5 closest matches
    # k = 5  # Number of nearest neighbors
    distances, indices = index.search(query_embedding, k)
    print(indices)
    indices = indices.flatten()
    print(indices, type(indices))
    texts, labels, scores = loadTexts()

    return [texts[i] for i in indices], [labels[i] for i in indices], [scores[i] for i in indices]
    # # Display results
    # print("\nTop 5 matches:")
    # for i, idx in enumerate(indices[0]):
    #     print(f"{i+1}. Text: {texts[idx]}")
    #     print(f"   Label: {labels[idx]}")
    #     print(f"   Score: {scores[idx]}")
    #     print(f"   Distance: {distances[0][i]}\n")