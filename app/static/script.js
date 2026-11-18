(() => {
  "use strict";

  // ---------------------------------------------------------------------
  // Element refs
  // ---------------------------------------------------------------------
  const fileInput = document.getElementById("fileInput");
  const dropzone = document.getElementById("dropzone");
  const dropzoneEmpty = document.getElementById("dropzoneEmpty");
  const previewWrap = document.getElementById("previewWrap");
  const previewImage = document.getElementById("previewImage");
  const scanLine = document.getElementById("scanLine");

  const analyzeBtn = document.getElementById("analyzeBtn");
  const analyzeBtnText = document.getElementById("analyzeBtnText");
  const analyzeSpinner = document.getElementById("analyzeSpinner");
  const resetBtn = document.getElementById("resetBtn");
  const errorBox = document.getElementById("errorBox");

  const emptyState = document.getElementById("emptyState");
  const results = document.getElementById("results");

  const finalPrediction = document.getElementById("finalPrediction");
  const finalBadge = document.getElementById("finalBadge");

  const stage1Badge = document.getElementById("stage1Badge");
  const probBenignText = document.getElementById("probBenignText");
  const probBenignBar = document.getElementById("probBenignBar");
  const probMalignantText = document.getElementById("probMalignantText");
  const probMalignantBar = document.getElementById("probMalignantBar");

  const stage2Card = document.getElementById("stage2Card");
  const stage2Badge = document.getElementById("stage2Badge");
  const stage2Bars = document.getElementById("stage2Bars");

  const recommendationText = document.getElementById("recommendationText");

  const SUBTYPE_LABELS = { mel: "Melanoma", bcc: "Basal Cell Carcinoma", akiec: "Actinic Keratosis" };

  let selectedFile = null;

  // ---------------------------------------------------------------------
  // File selection (click + drag & drop)
  // ---------------------------------------------------------------------
  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  function handleFile(file) {
    hideError();
    if (!file.type.startsWith("image/")) {
      showError("Please choose an image file (JPG, PNG, or WebP).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showError("File exceeds the 10MB limit.");
      return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImage.src = e.target.result;
      dropzoneEmpty.classList.add("d-none");
      previewWrap.classList.remove("d-none");
    };
    reader.readAsDataURL(file);

    analyzeBtn.disabled = false;
    resetResults();
  }

  // ---------------------------------------------------------------------
  // Analyze
  // ---------------------------------------------------------------------
  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    hideError();
    setLoading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("/predict", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Analysis failed. Please try again.");
      }
      renderResults(data);
    } catch (err) {
      showError(err.message || "Something went wrong while analyzing the image.");
    } finally {
      setLoading(false);
    }
  });

  resetBtn.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    dropzoneEmpty.classList.remove("d-none");
    previewWrap.classList.add("d-none");
    previewImage.src = "";
    analyzeBtn.disabled = true;
    resetBtn.classList.add("d-none");
    hideError();
    resetResults();
  });

  // ---------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------
  function renderResults(data) {
    emptyState.classList.add("d-none");
    results.classList.remove("d-none");
    resetBtn.classList.remove("d-none");

    const isMalignant = data.stage2 !== null;

    // Final diagnosis
    finalPrediction.textContent = data.final_prediction;
    finalBadge.textContent = isMalignant ? "Malignant" : "Benign";
    finalBadge.className = "final-badge " + (isMalignant ? "malignant" : "benign");

    // Stage 1
    const s1 = data.stage1;
    stage1Badge.textContent = s1.prediction;
    stage1Badge.className = "badge-outcome " + (s1.prediction === "Malignant" ? "badge-malignant" : "");
    probBenignText.textContent = pct(s1.probability_benign);
    probMalignantText.textContent = pct(s1.probability_malignant);
    requestAnimationFrame(() => {
      probBenignBar.style.width = pct(s1.probability_benign);
      probMalignantBar.style.width = pct(s1.probability_malignant);
    });

    // Stage 2
    if (isMalignant) {
      stage2Card.classList.remove("d-none");
      const s2 = data.stage2;
      stage2Badge.textContent = s2.prediction;

      stage2Bars.innerHTML = "";
      Object.entries(s2.probabilities).forEach(([code, prob]) => {
        const row = document.createElement("div");
        row.className = "confidence-row";
        row.innerHTML = `
          <div class="confidence-label">
            <span>${SUBTYPE_LABELS[code] || code}</span><span>${pct(prob)}</span>
          </div>
          <div class="progress"><div class="progress-bar bar-subtype" style="width:0%"></div></div>
        `;
        stage2Bars.appendChild(row);
        requestAnimationFrame(() => {
          row.querySelector(".progress-bar").style.width = pct(prob);
        });
      });
    } else {
      stage2Card.classList.add("d-none");
      stage2Bars.innerHTML = "";
    }

    // Recommendation
    recommendationText.textContent = data.recommendation;
  }

  function resetResults() {
    results.classList.add("d-none");
    emptyState.classList.remove("d-none");
    stage2Card.classList.add("d-none");
    stage2Bars.innerHTML = "";
    probBenignBar.style.width = "0%";
    probMalignantBar.style.width = "0%";
  }

  function pct(v) {
    return (v * 100).toFixed(1) + "%";
  }

  function setLoading(isLoading) {
    analyzeBtn.disabled = isLoading;
    analyzeBtnText.classList.toggle("d-none", isLoading);
    analyzeSpinner.classList.toggle("d-none", !isLoading);
    scanLine.classList.toggle("scanning", isLoading);
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.remove("d-none");
  }
  function hideError() {
    errorBox.classList.add("d-none");
  }
})();
