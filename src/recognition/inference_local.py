import os
import torch
import open_clip
from pathlib import Path
from PIL import Image
from .bioclip_base import BirdRecognizer
from typing import List, Dict, Any
import logging

class LocalBirdRecognizer(BirdRecognizer):
    def __init__(self, model_name: str = "imageomics/bioclip", device: str = None):
        if device is None or device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logging.info(f"Loading BioCLIP model '{model_name}' on {self.device}...")
        
        self.cached_labels = None
        self.cached_text_features = None

        try:
            self._load_model(model_name)
        except RuntimeError as e:
            if "CUDA" in str(e) and self.device != "cpu":
                logging.warning(f"CUDA initialization failed: {e}. Falling back to CPU.")
                self.device = "cpu"
                self._load_model(model_name)
            else:
                raise e

    def _load_model(self, model_name):
        import gc
        # Pre-emptive cleanup to avoid VRAM fragmentation causing spikes
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Check for local model
        local_model_path = Path("data/models/bioclip")
        
        # RTX 4060/Laptop Fix: Use fp16 for CUDA to reduce bandwidth spike/power surge
        precision = 'fp16' if self.device == 'cuda' else 'fp32'
        
        kwargs = {
            "precision": precision,
            "device": self.device
        }

        try:
            if local_model_path.exists():
                ckpt_path = local_model_path / "open_clip_pytorch_model.bin"
                if ckpt_path.exists():
                    logging.info(f"Loading from local checkpoint: {ckpt_path} (Precision: {precision})")
                    self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                        'ViT-B-16', 
                        pretrained=str(ckpt_path),
                        **kwargs
                    )
                else:
                    logging.warning(f"Local checkpoint not found at {ckpt_path}, trying hub load...")
                    self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                        'hf-hub:imageomics/bioclip',
                        **kwargs
                    )
            else:
                logging.info("Loading from Hugging Face Hub...")
                self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    'hf-hub:imageomics/bioclip',
                    **kwargs
                )
        except TypeError:
            # Fallback for older open_clip versions that might not support 'device' arg
            logging.warning("Installed open_clip might not support 'device' arg, falling back to manual transfer.")
            kwargs.pop("device")
            if local_model_path.exists() and (local_model_path / "open_clip_pytorch_model.bin").exists():
                 self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    'ViT-B-16', 
                    pretrained=str(local_model_path / "open_clip_pytorch_model.bin"),
                    **kwargs
                )
            else:
                 self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    'hf-hub:imageomics/bioclip',
                    **kwargs
                )
            self.model.to(self.device)
        
        # Ensure tokenizer is ready
        self.tokenizer = open_clip.get_tokenizer('ViT-B-16')
        logging.info("Model loaded successfully.")

    def _get_text_features(self, candidate_labels):
        # Check if cache is valid
        if self.cached_labels == candidate_labels and self.cached_text_features is not None:
            return self.cached_text_features

        logging.info(f"Encoding {len(candidate_labels)} text labels (this may take a moment)...")
        
        prompted_labels = [f"a photo of {label}, a type of bird." for label in candidate_labels]
        tokens = self.tokenizer(prompted_labels) # CPU tensor first
        
        # Batch processing to avoid OOM
        batch_size = 512 # Conservative batch size
        text_features_list = []
        
        device_type = 'cuda' if 'cuda' in self.device else 'cpu'
        
        with torch.no_grad(), torch.amp.autocast(device_type=device_type, enabled=(device_type == 'cuda')):
            for i in range(0, len(tokens), batch_size):
                batch_tokens = tokens[i : i + batch_size].to(self.device)
                batch_features = self.model.encode_text(batch_tokens)
                # Normalize immediately to save memory and prep for cosine sim
                batch_features /= batch_features.norm(dim=-1, keepdim=True)
                text_features_list.append(batch_features)
                
        # Concatenate all features
        all_text_features = torch.cat(text_features_list, dim=0)
        
        # Update Cache
        self.cached_labels = candidate_labels
        self.cached_text_features = all_text_features
        logging.info("Text features encoded and cached.")
        
        return all_text_features

    def predict(self, image_path: str, candidate_labels: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Predict using zero-shot classification via OpenCLIP.
        """
        if not candidate_labels:
            logging.warning("No candidate labels provided.")
            return []

        try:
            return self._do_predict(image_path, candidate_labels, top_k)
        except RuntimeError as e:
            if "CUDA" in str(e) and self.device != "cpu":
                logging.warning(f"CUDA prediction failed: {e}. Falling back to CPU for this request.")
                # Temp fallback for this object
                original_device = self.device
                self.device = "cpu"
                self.model.to("cpu")
                # Clear cache as device changed
                self.cached_text_features = None
                res = self._do_predict(image_path, candidate_labels, top_k)
                # Restore device (optional, but safer to stay on CPU if CUDA is unstable)
                # self.device = original_device
                # self.model.to(original_device)
                return res
            else:
                logging.error(f"Recognition error: {e}")
                return []

    def _do_predict(self, image_path, candidate_labels, top_k):
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # Get cached or new text features
        text_features = self._get_text_features(candidate_labels)

        # Use autocast to handle fp16/fp32 mismatches automatically
        # This is safer than manual casting for complex models like CLIP
        device_type = 'cuda' if 'cuda' in self.device else 'cpu'
        with torch.no_grad(), torch.amp.autocast(device_type=device_type, enabled=(device_type == 'cuda')):
            image_features = self.model.encode_image(image_input)
            
            # Ensure features are normalized for cosine similarity
            image_features /= image_features.norm(dim=-1, keepdim=True)
            # Text features are already normalized in _get_text_features

            text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)

        # Get top K
        top_probs, top_indices = text_probs[0].topk(min(top_k, len(candidate_labels)))
        
        results = []
        for prob, idx in zip(top_probs, top_indices):
            results.append({
                "scientific_name": candidate_labels[idx.item()],
                "confidence": prob.item()
            })
        
        return results

