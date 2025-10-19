import numpy as np
import faiss
from pathlib import Path

def build_index():
    """Create and save FAISS index."""
    print("Building FAISS index...")
    
    embeddings_path = Path("data/clip_embeddings_optimized.npy")
    output_path = Path("data/faiss_index.bin")
    
    if not embeddings_path.exists():
        print(f"Embeddings not found at {embeddings_path}")
        return
    
    embeddings = np.load(embeddings_path)
    print(f"Loaded embeddings: {embeddings.shape}")
    
    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    # Create index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype('float32'))
    
    # Save
    faiss.write_index(index, str(output_path))
    print(f"FAISS index saved: {output_path}")
    print(f"   Vectors: {index.ntotal}, Dimension: {dim}")

if __name__ == "__main__":
    build_index()
