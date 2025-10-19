import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from app.models.clip_loader import CLIPModelLoader
from app.services.indexer import FAISSIndexManager

class SearchEngine:
    """Production search engine with query enhancement."""
    
    def __init__(self, device: str = "cuda"):
        self.clip_loader = CLIPModelLoader(device=device)
        self.index_manager = FAISSIndexManager()
        self.query_enhancements = {
            "horse": "a horse animal standing in field or stable",
            "person": "a person standing or walking",
            "car": "a car vehicle on road or street",
            "cat": "a cat animal sitting or lying down",
            "dog": "a dog animal playing or sitting",
            "building": "a tall building architecture structure",
            "food": "delicious food meal on plate or table",
            "tree": "green tree in nature park or forest",
            "flower": "beautiful colorful flower in garden",
            "sunset": "beautiful sunset sky with orange and pink colors",
        }
    
    @classmethod
    def load_from_disk(cls, device: str = "cuda") -> "SearchEngine":
        """Load search engine with all components."""
        engine = cls(device=device)
        engine.clip_loader.load()
        engine.index_manager.load_from_disk()
        print("Search engine initialized successfully")
        return engine
    
    def enhance_query(self, query: str, use_enhancement: bool = True) -> List[str]:
        """Enhance query for better matching."""
        if not use_enhancement:
            return [query]
        
        enhanced = [query]
        q_lower = query.lower().strip()
        
        if " " not in q_lower and q_lower in self.query_enhancements:
            enhanced.append(self.query_enhancements[q_lower])
        
        if len(query.split()) == 1 and not query.startswith(('a ', 'an ', 'the ')):
            enhanced.append(f"a {query}")
        
        return enhanced[:3]
    
    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        threshold: float = 0.2,
        use_enhancement: bool = True
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Execute semantic search with query enhancement."""
        start_time = time.time()
        
        enhanced_queries = self.enhance_query(query, use_enhancement)
        all_results = {}
        
        for i, enhanced_query in enumerate(enhanced_queries):
            try:
                query_emb = self.clip_loader.encode_text(enhanced_query)
                query_np = query_emb.cpu().numpy()
                
                scores, indices = self.index_manager.search(query_np, top_k)
                weight = 1.0 - (i * 0.15)
                
                for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx >= 0 and idx < len(self.index_manager.valid_indices):
                        image_idx = int(self.index_manager.valid_indices[idx])
                        weighted_score = float(score) * weight
                        
                        if image_idx not in all_results:
                            all_results[image_idx] = {
                                'scores': [weighted_score],
                                'original_score': float(score),
                                'ranks': [rank]
                            }
                        else:
                            all_results[image_idx]['scores'].append(weighted_score)
                            all_results[image_idx]['ranks'].append(rank)
            
            except Exception as e:
                print(f"Error with query '{enhanced_query}': {e}")
                continue
        
        final_results = []
        for image_idx, data in all_results.items():
            max_score = max(data['scores'])
            avg_score = np.mean(data['scores'])
            num_matches = len(data['scores'])
            
            match_bonus = 1.0 + (num_matches - 1) * 0.1
            final_score = (max_score * 0.7 + avg_score * 0.3) * match_bonus
            
            if final_score >= threshold:
                image_path = self.index_manager.get_image_path(image_idx)
                filename = Path(image_path).name if image_path else f"img_{image_idx:05d}.jpg"
                
                final_results.append({
                    'rank': 0,
                    'image_idx': image_idx,
                    'filename': filename,
                    'image_path': image_path,
                    'similarity_score': final_score,
                    'confidence_percentage': f"{final_score*100:.1f}%",
                    'num_query_matches': num_matches,
                    'path': image_path
                })
        
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        for i, result in enumerate(final_results[:top_k]):
            result['rank'] = i + 1
        
        search_time = (time.time() - start_time) * 1000
        return final_results[:top_k], search_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get search engine status."""
        idx_status = self.index_manager.get_status()
        return {
            "device": self.clip_loader.device,
            "model": self.clip_loader.model_name,
            **idx_status
        }
