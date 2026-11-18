# Shama (شامة): Two-Stage AI Skin Lesion Analysis

Shama is a web application that analyzes a dermoscopic image of a skin lesion in two stages. First it screens the lesion as **benign or malignant**. If the lesion looks malignant, it then identifies the **cancer subtype**. The app is built on the HAM10000 dataset and fine-tuned EfficientNet-B3 models, and it is served with FastAPI.

This was our graduation project. I led the team.

> **Live demo:** [huggingface.co/spaces/aishaalsadani/shama](https://huggingface.co/spaces/aishaalsadani/shama)

> ⚠️ **Shama is a research and education project, not a medical device.** Its output is not a diagnosis. Anyone worried about a skin lesion should see a dermatologist.

---

## How it works

```
                 ┌───────────────────────────────┐
  Uploaded  ───► │  Stage 1: Binary screening    │ ──► Benign ──► final result
   image         │  EfficientNet-B3 (1 output)   │
                 └──────────────┬────────────────┘
                                │ Malignant
                                ▼
                 ┌───────────────────────────────┐
                 │  Stage 2: Malignant subtype   │ ──► Melanoma (mel)
                 │  EfficientNet-B3 (3 outputs)  │ ──► Basal Cell Carcinoma (bcc)
                 └───────────────────────────────┘ ──► Actinic Keratosis / Intraepithelial Carcinoma (akiec)
```

- Stage 1 runs on every image. Stage 2 runs only when Stage 1 says the lesion is malignant. The backend makes that decision, not the user.
- Both stages use the same preprocessing: resize to 320 px (bicubic), center-crop to 300 px, and ImageNet normalization.
- Both stages use **3-view test-time augmentation**: the original image plus a horizontal flip and a vertical flip, averaged.
- Each result comes with a recommendation in plain language. The app also has a **dataset analytics dashboard** that shows the HAM10000 class, age, sex and body-location distributions.

## Results (held-out test set)

The test set was scored **once**, after the models and thresholds were locked using the validation set only. Lesion IDs were checked so that no lesion appears in both splits.

### Stage 1: Benign vs Malignant (2,147 test images)

| Metric | EfficientNet-B3 (deployed) |
|---|---|
| ROC-AUC | **0.948** |
| PR-AUC | 0.898 |
| Accuracy | 0.887 |
| Balanced accuracy | 0.871 |
| Malignant recall (sensitivity) | 0.826 |
| Specificity | 0.915 |
| Malignant F1 | 0.822 |

### Stage 2: Malignant subtype, mel / bcc / akiec (674 test images)

| Metric | EfficientNet-B3 (deployed) |
|---|---|
| Macro ROC-AUC (one-vs-rest) | **0.965** |
| Macro PR-AUC | 0.916 |
| Accuracy | 0.871 |
| Balanced accuracy | 0.861 |
| Macro F1 | 0.855 |

### Backbones compared for Stage 1

| Backbone | ROC-AUC | Balanced accuracy | Malignant recall | Specificity |
|---|---|---|---|---|
| **EfficientNet-B3** (selected) | **0.948** | **0.871** | 0.826 | **0.915** |
| DINOv2 (ViT) | 0.930 | 0.841 | 0.806 | 0.876 |
| DenseNet121 | 0.917 | 0.830 | 0.804 | 0.856 |

The team also tested a **late-fusion model** that combines image features with patient metadata (age, sex, lesion location), and a **validation-optimized weighted ensemble** of the three backbones. You can find both in [`notebooks/fusion_and_ensemble`](notebooks/fusion_and_ensemble).

## Tech stack

- **Modeling:** PyTorch, torchvision (EfficientNet-B3, DenseNet121), DINOv2, scikit-learn
- **Serving:** FastAPI, Uvicorn, Jinja2
- **Frontend:** HTML, CSS, JavaScript, Bootstrap, Chart.js
- **Deployment:** Docker, Hugging Face Spaces
- **Data:** [HAM10000](https://doi.org/10.7910/DVN/DBW86T), about 10,000 dermoscopic images in 7 diagnostic classes

## Repository structure

```
Shama/
├── app/                         # The web application (FastAPI + Docker)
│   ├── app.py                   # Routes: /, /dashboard, /api/dashboard, /health, /predict
│   ├── config.py                # App settings + Stage 2 config
│   ├── config_binary.py         # Stage 1 config
│   ├── model*.py                # EfficientNet-B3 architectures + checkpoint loading
│   ├── preprocessing*.py        # Image transforms (identical to training)
│   ├── inference*.py            # Predictors with 3-view TTA
│   ├── dataset_stats.py         # Dashboard statistics from HAM10000 metadata
│   ├── models/                  # best_model.pth (Stage 1), best_model_m.pth (Stage 2)
│   ├── data/                    # HAM10000_metadata.csv
│   ├── templates/  static/      # UI
│   ├── requirements.txt
│   └── Dockerfile
└── notebooks/
    ├── binary/                  # Stage 1 experiments: EfficientNet-B3, DenseNet121, DINOv2
    ├── multiclass/              # Stage 2 subtype model
    └── fusion_and_ensemble/     # Metadata late fusion + weighted ensemble
```

## Run locally

**With Docker**

```bash
cd app
docker build -t shama .
docker run -p 8000:8000 shama
```

**Without Docker**

```bash
cd app
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000.

## API

```bash
curl -X POST -F "file=@lesion.jpg" http://localhost:8000/predict
```

The endpoint accepts JPEG, PNG or WebP images up to 10 MB. It returns Stage 1 probabilities, Stage 2 subtype probabilities (only when Stage 1 says malignant), the final prediction and a recommendation.

## Known limitations

- **Stage 1 calibration.** In the training notebook, Stage 1 probabilities were calibrated with Platt scaling, and the decision threshold was then tuned on validation. The fitted calibrator was not saved in the checkpoint. So the app uses the raw sigmoid with a 0.5 threshold, which means its confidence scores are uncalibrated.
- **Dataset bias.** HAM10000 is mostly lighter skin types and dermoscopic images. Performance on darker skin, or on ordinary phone photos, has not been validated.
- **Stage 2 covers three malignant subtypes only.** Rarer malignancies are outside its scope.

## Team

Graduation project. **Aisha Alsadani** was team lead.

---

*Built with care for early detection.*
