import torch
import clip
from typing import Tuple

class CLIPModelLoader:
    """Manages CLIP model loading and text encoding."""
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = "cuda"):
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        print(f"Initializing CLIP on {self.device}")
        
    def load(self) -> Tuple[torch.nn.Module, object]:
        """Load CLIP model and preprocessing."""
        if self.model is None:
            print(f"Loading {self.model_name}...")
            self.model, self.preprocess = clip.load(self.model_name, device=self.device)
            self.model.eval()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                print(f"GPU Memory: {gpu_mem:.2f} GB")
        
        return self.model, self.preprocess
    
    def encode_text(self, text: str) -> torch.Tensor:
        """Encode text to normalized embedding."""
        if self.model is None:
            self.load()
        
        with torch.no_grad():
            tokens = clip.tokenize([text], truncate=True).to(self.device)
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        
        return features
