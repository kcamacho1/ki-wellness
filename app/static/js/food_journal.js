// static/js/food_journal.js

window.addEventListener("load", () => {
  initFormToggles();
  initCSVUpload();
  initDeleteSelected();
  initSelectAll();
  initDateFilter();
  initViewToggle();
  initCSVDownload();
  initAddFoodForm();

});

function initFormToggles() {
  const formBtn = document.getElementById("toggleFormButton");
  const filtersBtn = document.getElementById("toggleFiltersButton");
  const entryForm = document.getElementById("entryForm");
  const dateFilters = document.getElementById("dateFilters");

  if (!formBtn || !filtersBtn || !entryForm || !dateFilters) {
    console.warn("[initFormToggles] One or more elements not found.");
    return;
  }

  formBtn.addEventListener("click", () => {
    entryForm.classList.toggle("hidden");
    if (!entryForm.classList.contains("hidden")) dateFilters.classList.add("hidden");
  });

  filtersBtn.addEventListener("click", () => {
    dateFilters.classList.toggle("hidden");
    if (!dateFilters.classList.contains("hidden")) entryForm.classList.add("hidden");
  });
}

function initSelectAll() {
  const selectAll = document.getElementById("selectAll");
  const checkboxes = document.querySelectorAll(".entryCheckbox");

  if (!selectAll || checkboxes.length === 0) {
    console.warn("[initSelectAll] selectAll or checkboxes missing");
    return;
  }

  selectAll.addEventListener("change", e => {
    checkboxes.forEach(cb => cb.checked = e.target.checked);
  });
}

function initCSVUpload() {
  const uploadInput = document.getElementById("uploadCsvInput");
  if (!uploadInput) {
    console.warn("[initCSVUpload] uploadCsvInput not found");
    return;
  }

  uploadInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return showToast("No file selected.", "error");

    const text = await file.text();
    const rows = text.trim().split("\n").slice(1);

    function parseCSVRow(line) {
      const regex = /(?:\"([^\"]*)\")|([^,]+)/g;
      const result = [];
      let match;
      while ((match = regex.exec(line)) !== null) {
        result.push(match[1] ?? match[2]);
      }
      return result;
    }

    const entries = rows.map(line => {
      const [Date, MealType, Food, ServingRaw, Calories, Protein, Carbs, Fat, Mood, Notes] = parseCSVRow(line);
      const [servings, ...unitParts] = ServingRaw.trim().split(" ");
      const serving_unit = unitParts.join(" ");

      return {
        date_logged: Date,
        meal_type: MealType,
        food_name: Food,
        servings: parseFloat(servings),
        serving_unit,
        calories: parseFloat(Calories),
        protein: parseFloat(Protein.replace("g", "")),
        carbs: parseFloat(Carbs.replace("g", "")),
        fat: parseFloat(Fat.replace("g", "")),
        mood: Mood,
        notes: Notes || ""
      };
    });

    const res = await fetch("/upload-csv-entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries })
    });

    if (res.ok) {
      showToast("CSV uploaded successfully.");
      setTimeout(() => window.location.reload(), 1500);
    } else {
      showToast("Failed to upload CSV.", "error");
    }
  });
}

function initDeleteSelected() {
  const deleteBtn = document.getElementById("deleteSelectedBtn");

  if (!deleteBtn) {
    console.warn("[initDeleteSelected] deleteSelectedBtn not found");
    return;
  }

  deleteBtn.addEventListener("click", async () => {
    const selected = document.querySelectorAll(".entryCheckbox:checked");
    if (!selected.length) return showToast("No entries selected.", "error");

    const ids = Array.from(selected).map(cb => cb.dataset.id);
    const res = await fetch("/delete-food-entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids })
    });
    if (res.ok) {
      showToast(`${ids.length} entries deleted.`);
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast("Failed to delete.", "error");
    }
  });
}

function initDateFilter() {
  const applyBtn = document.getElementById("applyFiltersBtn");

  if (!applyBtn) {
    console.warn("[initDateFilter] applyFiltersBtn not found");
    return;
  }

  applyBtn.addEventListener("click", () => {
    const start = document.getElementById("dateStart").value;
    const end = document.getElementById("dateEnd").value;
    if (!start || !end) return showToast("Select both dates.", "error");
    window.location.href = `/food-journal?start=${start}&end=${end}`;
  });
}

function initViewToggle() {
  const toggleBtn = document.getElementById("toggleViewButton");
  const table = document.getElementById("tableView");
  const chart = document.getElementById("chartView");

  if (!toggleBtn || !table || !chart) {
    console.warn("[initViewToggle] toggleViewButton or view sections not found");
    return;
  }

  toggleBtn.addEventListener("click", () => {
    table.classList.toggle("hidden");
    chart.classList.toggle("hidden");
    toggleBtn.innerText = chart.classList.contains("hidden") ? "📊 View Chart" : "📋 View Table";
  });
}

function initCSVDownload() {
  const downloadBtn = document.getElementById("downloadRangeBtn");
  downloadBtn?.addEventListener("click", () => {
    const rows = [["Date", "Meal Type", "Food", "Servings", "Calories", "Protein", "Carbs", "Fat", "Mood", "Notes"]];
    document.querySelectorAll("tbody tr").forEach(row => {
      const cells = Array.from(row.querySelectorAll("td")).map(td => td.innerText.trim());
      rows.push(cells.slice(1)); // skip checkbox
    });

    const csv = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "food-journal.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("CSV downloaded!");
  });
}

function initAddFoodForm() {
  const form = document.getElementById("addFoodForm");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const res = await fetch("/add-food-entry", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (res.ok) {
      showToast("Food entry added!");
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast("Error adding food.", "error");
    }
  });
}


function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toast-message");
  if (!toast || !toastMsg) return;

  toastMsg.textContent = message;
  toast.classList.remove("bg-emerald-600", "bg-rose-600", "opacity-0");
  toast.classList.add(type === "error" ? "bg-rose-600" : "bg-emerald-600", "opacity-100");
  setTimeout(() => toast.classList.add("opacity-0"), 2500);
}