# ai_engine/src/knowledge_tracing/calibration/calibrator.py
from __future__ import annotations
import torch
import numpy as np
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger("calibrator")

class TemperatureScalingCalibrator:
    """
    Maintains temperature parameters segmented by (exam_code, subject)
    to avoid cross-exam/subject miscalibration.
    """
    def __init__(self):
        self._temps: Dict[Tuple[str, str], torch.nn.Parameter] = {}
        self._fitted: Dict[Tuple[str, str], bool] = {}

    def _key(self, exam_code: str, subject: str) -> Tuple[str, str]:
        return (exam_code or "JEE_Mains", subject or "generic")

    def get_temperature(self, exam_code: str, subject: str) -> float:
        key = self._key(exam_code, subject)
        if key not in self._temps:
            self._temps[key] = torch.nn.Parameter(torch.ones(1))
            self._fitted[key] = False
        return float(self._temps[key].item())

    def fit(self, logits: torch.Tensor, labels: torch.Tensor, exam_code: str, subject: str,
            max_iter: int = 50, lr: float = 0.01, verbose: bool = False) -> float:
        key = self._key(exam_code, subject)
        if key not in self._temps:
            self._temps[key] = torch.nn.Parameter(torch.ones(1))
            self._fitted[key] = False

        temp = self._temps[key]
        optimizer = torch.optim.LBFGS([temp], lr=lr, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            scaled = logits / temp
            loss = torch.nn.functional.cross_entropy(scaled, labels)
            loss.backward()
            if verbose:
                logger.info(f"[Calib] {key} loss={loss.item():.6f} T={temp.item():.4f}")
            return loss

        optimizer.step(closure)
        self._fitted[key] = True
        logger.info(f"[Calib] Fitted temperature {key}: {temp.item():.4f}")
        return float(temp.item())

    def calibrate(self, logits: torch.Tensor, exam_code: str, subject: str) -> torch.Tensor:
        key = self._key(exam_code, subject)
        if key not in self._temps or not self._fitted.get(key, False):
            logger.warning(f"[Calib] Using uncalibrated softmax for {key}")
            return torch.softmax(logits, dim=1)
        T = self._temps[key]
        return torch.softmax(logits / T, dim=1)

    def expected_calibration_error(self, probs: torch.Tensor, labels: torch.Tensor, n_bins: int = 10) -> float:
        """
        Compute Expected Calibration Error (ECE).

        Args:
            probs: model predicted probabilities (N x C)
            labels: true label indices (N,)
            n_bins: number of bins

        Returns:
            ECE scalar
        """
        confidences, predictions = torch.max(probs, 1)
        accuracies = predictions.eq(labels)

        bin_boundaries = torch.linspace(0, 1, n_bins + 1)
        ece = torch.tensor(0.0)

        for lower, upper in zip(bin_boundaries[:-1], bin_boundaries[1:]):
            in_bin = (confidences > lower.item()) & (confidences <= upper.item())
            prop_in_bin = in_bin.float().mean()
            if prop_in_bin.item() > 0:
                accuracy_in_bin = accuracies[in_bin].float().mean()
                avg_confidence_in_bin = confidences[in_bin].mean()
                ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        return ece.item()

CALIBRATOR_REGISTRY = TemperatureScalingCalibrator()