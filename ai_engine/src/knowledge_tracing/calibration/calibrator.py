# ai_engine/src/knowledge_tracing/calibration/calibrator.py
from __future__ import annotations
import torch
import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger("calibrator")

class TemperatureScalingCalibrator:
    """
    Temperature scaling calibrator for neural network logits.
    Fits temperature parameter to validation logits and labels
    to improve probability calibration.
    """

    def __init__(self):
        self.temperature = torch.nn.Parameter(torch.ones(1))
        self.fitted = False

    def _nll(self, scaled_logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Compute negative log-likelihood loss (cross-entropy).
        """
        log_probs = torch.nn.functional.log_softmax(scaled_logits, dim=1)
        loss = torch.nn.functional.nll_loss(log_probs, labels)
        return loss

    def fit(self, logits: torch.Tensor, labels: torch.Tensor, max_iter: int = 50, lr: float = 0.01, verbose: bool = False):
        """
        Optimize temperature using gradient descent.

        Args:
            logits: raw logits (N x C)
            labels: true labels (N,)
        """
        optimizer = torch.optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            scaled_logits = logits / self.temperature
            loss = self._nll(scaled_logits, labels)
            loss.backward()
            if verbose:
                logger.info(f"Loss {loss.item()} Temperature {self.temperature.item()}")
            return loss

        optimizer.step(closure)
        self.fitted = True
        logger.info(f"Fitted temperature scaler: {self.temperature.item():.4f}")

    def calibrate(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Apply temperature scaled softmax probabilities.

        Args:
            logits: raw logits (N x C)

        Returns:
            calibrated probabilities (N x C)
        """
        if not self.fitted:
            logger.warning("TemperatureScalingCalibrator calibrate called before fit.")
            return torch.softmax(logits, dim=1)
        scaled_logits = logits / self.temperature
        return torch.softmax(scaled_logits, dim=1)

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
