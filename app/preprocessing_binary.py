"""
preprocessing_binary.py
Stage 1 image transform pipeline - the exact resize/crop/normalize/TTA recipe used in
Binary_EfficientNetB3_Baseline_V2.ipynb (Section 10), built from config_binary.py (in turn
resolved from the checkpoint's own saved config, not hand-picked).
"""
from typing import List

from PIL import Image
from torchvision import transforms
from torchvision.transforms import InterpolationMode

from config_binary import (
    STAGE1_RESIZE_SIZE,
    STAGE1_IMG_SIZE,
    STAGE1_NORM_MEAN,
    STAGE1_NORM_STD,
    STAGE1_INTERPOLATION,
)

_interp = InterpolationMode.BICUBIC if STAGE1_INTERPOLATION == "bicubic" else InterpolationMode.BILINEAR


def _build_eval_transform(hflip: bool = False, vflip: bool = False) -> transforms.Compose:
    ops = []
    if hflip:
        ops.append(transforms.RandomHorizontalFlip(p=1.0))  # p=1.0 -> always applied (fixed flip, not augmentation)
    if vflip:
        ops.append(transforms.RandomVerticalFlip(p=1.0))
    ops += [
        transforms.Resize(STAGE1_RESIZE_SIZE, interpolation=_interp),
        transforms.CenterCrop(STAGE1_IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=STAGE1_NORM_MEAN, std=STAGE1_NORM_STD),
    ]
    return transforms.Compose(ops)


# Base (no-augmentation) eval transform + the 3-view TTA set (identity, h-flip, v-flip) -
# identical scheme to training/evaluation in the notebook.
eval_transform = _build_eval_transform()
tta_transforms: List[transforms.Compose] = [
    eval_transform,
    _build_eval_transform(hflip=True),
    _build_eval_transform(vflip=True),
]


def preprocess_image(image: Image.Image) -> list:
    """Applies each of the 3 TTA-view transforms to a single PIL image (RGB) and returns a
    list of transformed tensors, one per view, ready to be stacked into a batch."""
    image = image.convert("RGB")
    return [t(image) for t in tta_transforms]
