"""
inference_binary.py
Stage 1 inference: EfficientNet-B3 binary classifier with 3-view TTA, matching the inference
procedure in Binary_EfficientNetB3_Baseline_V2.ipynb (Section 13), minus Platt calibration
(see config_binary.py docstring for why that step is not reproducible from the checkpoint).
"""
import logging

import torch
from PIL import Image

from config_binary import STAGE1_CLASSES, STAGE1_THRESHOLD, STAGE1_RECOMMENDATIONS
from model_binary import load_binary_model
from preprocessing_binary import preprocess_image

logger = logging.getLogger("inference_binary")


class Stage1Predictor:
    """Loads the Stage 1 model once at startup and reuses it for every request."""

    def __init__(self, device: torch.device):
        self.device = device
        self.model = load_binary_model(device)
        logger.info("Stage 1 (binary) model loaded on %s", device)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        views = preprocess_image(image)                 # 3 TTA-view tensors
        batch = torch.stack(views).to(self.device)       # (3, C, H, W)
        logits = self.model(batch)                        # (3,)
        probs = torch.sigmoid(logits).cpu().numpy()
        probability_malignant = float(probs.mean())        # TTA average
        probability_benign = 1.0 - probability_malignant

        is_malignant = probability_malignant >= STAGE1_THRESHOLD
        label = STAGE1_CLASSES[1] if is_malignant else STAGE1_CLASSES[0]
        confidence = probability_malignant if is_malignant else probability_benign

        return {
            "prediction": label,
            "confidence": round(confidence, 4),
            "probability_benign": round(probability_benign, 4),
            "probability_malignant": round(probability_malignant, 4),
            "is_malignant": is_malignant,
            "recommendation": STAGE1_RECOMMENDATIONS[label],
        }
