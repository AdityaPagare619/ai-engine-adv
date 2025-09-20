# ai_engine/src/knowledge_tracing/models/sakt_model.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import torch
except ImportError:
    torch = None


class SAKTTorchAdapter:
    """
    Thin adapter around a loaded PyTorch SAKT model providing a uniform
    predict_correctness_prob(sequence) interface for ensembling.
    """

    def __init__(self, torch_model: Any, device: str = "cpu"):
        self.model = torch_model
        self.device = device
        self.model.eval()

    @staticmethod
    def _to_tensor(seq: List[Dict[str, Any]]):
        """
        Convert sequence of {question_id, is_correct, ...} to model tensors.
        Must match the preprocessing used during training.
        """
        # Placeholder: implement your ID mapping and tensorization here.
        # Return a dict of tensors compatible with model.forward().
        return {}

    def predict_correctness_prob(self, sequence: List[Dict[str, Any]]) -> float:
        if torch is None:
            raise RuntimeError("Torch not available. Install PyTorch to use SAKT model.")

        with torch.no_grad():
            batch = self._to_tensor(sequence)
            # Move tensors to device if needed
            batch = {k: v.to(self.device) for k, v in batch.items()} if batch else {}

            out = self.model(**batch)  # expected to return probabilities or logits

            try:
                prob = float(out)  # when model returns scalar tensor probability
            except Exception:
                # Assume dict-like output
                prob = float(out["prob"])
            return max(0.0, min(1.0, prob))


def load_pytorch_sakt(weights_path: str, device: str = "cpu") -> SAKTTorchAdapter:
    """
    Loads a PyTorch SAKT model checkpoint and returns an adapter.
    """
    if torch is None:
        raise RuntimeError("Torch not available. Install PyTorch to load SAKT model.")

    ckpt = torch.load(weights_path, map_location=device)
    model = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
    return SAKTTorchAdapter(torch_model=model, device=device)


class SAKTAttentionModel:
    """
    Self-Attentive Knowledge Tracing (Pandey & Karypis, 2019) inference model.
    Supports both a naive smoothing baseline and a real PyTorch adapter.
    """

    def __init__(self, max_len: int = 200):
        self.max_len = max_len
        self.is_loaded = False
        self._adapter: Optional[SAKTTorchAdapter] = None

    def load(self, weights_path: str, device: str = "cpu") -> None:
        """
        Load trained PyTorch weights and attach adapter.
        """
        self._adapter = load_pytorch_sakt(weights_path, device)
        self.is_loaded = True

    def predict_correctness_prob(
        self,
        sequence: List[Dict[str, Any]]
    ) -> float:
        """
        sequence: [{ 'question_id': str, 'is_correct': int, 'timestamp': str, ... }, ...]
        Returns a probability in [0,1] for the next interaction being correct.
        """
        if self.is_loaded and self._adapter is not None:
            try:
                return self._adapter.predict_correctness_prob(sequence)
            except Exception as e:
                # Fallback gracefully if adapter prediction fails
                print(f"[Warning] Adapter prediction failed: {e}. Falling back to baseline.")

        # --- Fallback baseline ---
        k = min(len(sequence), self.max_len)
        recent = sequence[-k:]
        if not recent:
            return 0.6
        avg = np.mean([1.0 if r.get("is_correct", 0) else 0.0 for r in recent])
        return float(0.6 * 0.5 + avg * 0.5)
