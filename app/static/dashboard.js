(() => {
  "use strict";

  const loadingEl = document.getElementById("datasetLoading");
  const errorEl = document.getElementById("datasetError");
  const bodyEl = document.getElementById("datasetBody");

  if (!bodyEl) return;

  // تأكد من تحميل Chart.js
  if (typeof Chart === "undefined") {
    loadingEl.classList.add("d-none");
    errorEl.textContent =
      "Chart.js library failed to load. Please refresh the page.";
    errorEl.classList.remove("d-none");
    console.error("Chart.js is not loaded.");
    return;
  }

  const PALETTE = [
    "#3B82F6",
    "#22D3EE",
    "#34D399",
    "#FBBF24",
    "#F87171",
    "#A78BFA",
    "#F472B6",
    "#60A5FA"
  ];

  const GRID_COLOR = "rgba(148,163,195,0.12)";
  const TEXT_COLOR = "#8B96AC";

  Chart.defaults.color = TEXT_COLOR;
  Chart.defaults.font.family = "'Inter', sans-serif";

  async function loadDashboard() {
    try {
      const res = await fetch("/api/dashboard");

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      render(data);

    } catch (err) {

      console.error(err);

      loadingEl.classList.add("d-none");

      errorEl.textContent =
        "Could not load dataset statistics.";

      errorEl.classList.remove("d-none");
    }
  }

  function render(data) {

    loadingEl.classList.add("d-none");
    bodyEl.classList.remove("d-none");

    document.getElementById("statTotalImages").textContent =
      data.total_images.toLocaleString();

    document.getElementById("statAverageAge").textContent =
      data.average_age ?? "N/A";

    const male = data.gender_distribution.male || 0;
    const female = data.gender_distribution.female || 0;

    document.getElementById("statGenderSplit").textContent =
      `${male} / ${female}`;

    document.getElementById("statClassCount").textContent =
      Object.keys(data.class_distribution).length;

    document.getElementById("statLocationCount").textContent =
      Object.keys(data.body_locations).length;

    doughnut(
      "chartClassDistribution",
      data.class_distribution
    );

    pie(
      "chartGender",
      data.gender_distribution
    );

    bar(
      "chartDiagnosisTypes",
      data.diagnosis_types,
      "y"
    );

    bar(
      "chartBodyLocations",
      data.body_locations,
      "y"
    );

    histogram(
      "chartAgeDistribution",
      data.age_distribution.bins,
      data.age_distribution.counts
    );
  }

  function colors(n) {
    return Array.from(
      { length: n },
      (_, i) => PALETTE[i % PALETTE.length]
    );
  }

  function doughnut(id, dict) {

    new Chart(document.getElementById(id), {

      type: "doughnut",

      data: {
        labels: Object.keys(dict),
        datasets: [{
          data: Object.values(dict),
          backgroundColor: colors(Object.keys(dict).length),
          borderWidth: 0
        }]
      },

      options: {
        responsive: true,
        maintainAspectRatio: false
      }

    });

  }

  function pie(id, dict) {

    new Chart(document.getElementById(id), {

      type: "pie",

      data: {
        labels: Object.keys(dict),
        datasets: [{
          data: Object.values(dict),
          backgroundColor: colors(Object.keys(dict).length),
          borderWidth: 0
        }]
      },

      options: {
        responsive: true,
        maintainAspectRatio: false
      }

    });

  }

  function bar(id, dict, axis) {

    const entries = Object.entries(dict)
      .sort((a, b) => b[1] - a[1]);

    new Chart(document.getElementById(id), {

      type: "bar",

      data: {
        labels: entries.map(e => e[0]),
        datasets: [{
          data: entries.map(e => e[1]),
          backgroundColor: "#3B82F6",
          borderRadius: 4
        }]
      },

      options: {

        indexAxis: axis,

        responsive: true,

        maintainAspectRatio: false,

        plugins: {
          legend: {
            display: false
          }
        }

      }

    });

  }

  function histogram(id, bins, counts) {

    new Chart(document.getElementById(id), {

      type: "bar",

      data: {

        labels: bins,

        datasets: [{

          data: counts,

          backgroundColor: "#22D3EE",

          borderRadius: 4

        }]

      },

      options: {

        responsive: true,

        maintainAspectRatio: false,

        plugins: {

          legend: {

            display: false

          }

        }

      }

    });

  }

  loadDashboard();

})();
