"""
config_binary.py
Stage 1 (Binary: Benign vs Malignant) model configuration.

Preprocessing values below mirror best_model.pth's saved `config` dict exactly - resolved at
training time from torchvision's official `EfficientNet_B3_Weights.IMAGENET1K_V1` transform
metadata (Binary_EfficientNetB3_Baseline_V2.ipynb, Section 9), never hand-picked.

IMPORTANT - calibration note:
The training notebook fits a Platt-scaling calibrator (an sklearn LogisticRegression) on the
validation set's raw sigmoid outputs, then searches an F1-optimal decision threshold (0.69) on
the *calibrated* probabilities. That calibrator's fitted parameters (A, B) were NOT included in
best_model.pth - the checkpoint only saved `model_state`, `config`, `best_epoch`,
`best_val_auc`, and `best_threshold` - so the calibration step cannot be reproduced exactly from
the checkpoint alone. Rather than apply the 0.69 threshold to uncalibrated probabilities (which
would silently shift the decision boundary in an unverified direction), this backend serves the
model's raw sigmoid output with the standard 0.5 threshold and reports it explicitly as an
uncalibrated confidence score. If the fitted Platt calibrator is recovered later (e.g. it was
also pickled during training), load it in `inference_binary.py` and restore
STAGE1_THRESHOLD = 0.69 below.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

STAGE1_MODEL_PATH = MODELS_DIR / "best_model.pth"

STAGE1_RESIZE_SIZE = 320
STAGE1_IMG_SIZE = 300
STAGE1_NORM_MEAN = [0.485, 0.456, 0.406]
STAGE1_NORM_STD = [0.229, 0.224, 0.225]
STAGE1_INTERPOLATION = "bicubic"

STAGE1_CLASSES = ["Benign", "Malignant"]

# See module docstring - calibrator not recoverable from the checkpoint, so this is the
# standard 0.5 threshold on raw (uncalibrated) sigmoid probability, not the notebook's 0.69.
STAGE1_THRESHOLD = 0.5
STAGE1_CALIBRATED = False

STAGE1_USE_TTA = True  # 3-view TTA: identity, horizontal flip, vertical flip

STAGE1_RECOMMENDATIONS = {
    "Benign": (
        "The lesion is classified as benign, with no malignant features detected. Routine "
        "skin self-checks are recommended; consult a dermatologist if you notice changes in "
        "size, shape, color, or symptoms over time."
    ),
    "Malignant": (
        "The lesion shows features suggestive of malignancy. It has been automatically routed "
        "to subtype analysis below. Please consult a dermatologist promptly."
    ),
}
