"""
model_binary.py
Stage 1 architecture - EfficientNet-B3 binary classifier.

Extracted exactly from Binary_EfficientNetB3_Baseline_V2.ipynb (Section 9):
backbone = torchvision.models.efficientnet_b3, classifier head replaced with
Dropout(0.3) -> Linear(in_features, 1), forward() squeezes to a single logit per image.
best_model.pth's `model_state` was produced by this exact class - layer names and shapes
must match exactly for `load_state_dict` to succeed.
"""
import torch
import torch.nn as nn
import torchvision

from config_binary import STAGE1_MODEL_PATH


class EfficientNetB3BinaryClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        # weights=None: we load fine-tuned weights from the checkpoint right after, so there is
        # no need to download ImageNet-pretrained weights at inference/server startup time.
        self.backbone = torchvision.models.efficientnet_b3(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 1),
        )

    def forward(self, x):
        return self.backbone(x).squeeze(1)


def load_binary_model(device: torch.device) -> EfficientNetB3BinaryClassifier:
    """Instantiates the Stage 1 architecture and loads best_model.pth's weights onto it."""
    if not STAGE1_MODEL_PATH.exists():
        raise FileNotFoundError(f"Stage 1 checkpoint not found at {STAGE1_MODEL_PATH}")

    checkpoint = torch.load(STAGE1_MODEL_PATH, map_location=device, weights_only=False)
    model = EfficientNetB3BinaryClassifier()
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    return model
