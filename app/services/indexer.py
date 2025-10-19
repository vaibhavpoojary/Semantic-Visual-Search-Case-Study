import json
import numpy as np
import faiss
from pathlib import Path
from typing import Dict, Any, Tuple

class FAISSIndexManager:
    """Manages FAISS index loading and search operations."""
    
    def __init__(self):
        self.index = None
        self.embeddings = None
        self.valid_indices = None
        self.metadata = None
        self.image_paths = []
        
    def load_from_disk(
        self,
        embeddings_path: str = "data/clip_embeddings_optimized.npy",
        faiss_index_path: str = "data/faiss_index.bin",
        metadata_path: str = "data/embedding_metadata.json",
        indices_path: str = "data/valid_indices.npy"
    ) -> None:
        """Load all index components from disk."""
        print("Loading embeddings and index...")
        
        # Load embeddings
        self.embeddings = np.load(embeddings_path)
        print(f"Loaded embeddings: {self.embeddings.shape}")
        
        # Load or create FAISS index
        if Path(faiss_index_path).exists():
            self.index = faiss.read_index(faiss_index_path)
            print(f"Loaded FAISS index: {self.index.ntotal} vectors")
        else:
            print("FAISS index not found, creating new...")
            self.index = self._create_index(self.embeddings)
            faiss.write_index(self.index, faiss_index_path)
            print(f"Created and saved FAISS index")
        
        # Load valid indices
        self.valid_indices = np.load(indices_path)
        print(f"Loaded {len(self.valid_indices)} valid indices")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.image_paths = self.metadata.get("image_paths", [])
        print(f"Loaded {len(self.image_paths)} image paths")
    
    def _create_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Create normalized FAISS index."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype('float32'))
        return index
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar images."""
        if self.index is None:
            raise ValueError("Index not loaded")
        
        scores, indices = self.index.search(
            query_embedding.astype('float32'), 
            top_k * 3
        )
        return scores, indices
    
    def get_image_path(self, idx: int) -> str:
        """Get image path by index."""
        return self.image_paths[idx] if 0 <= idx < len(self.image_paths) else ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get index status."""
        return {
            "vectors_indexed": self.index.ntotal if self.index else 0,
            "embedding_dim": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "total_images": len(self.image_paths),
            "index_type": type(self.index).__name__ if self.index else "None"
        }
