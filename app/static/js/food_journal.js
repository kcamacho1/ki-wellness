document.addEventListener('DOMContentLoaded', () => {
  const aiSummaryBtn = document.getElementById('aiSummaryBtn');
  if (aiSummaryBtn) {
    aiSummaryBtn.addEventListener('click', async () => {
      showLoader();

      try {
        const response = await fetch("/api/food_journal/summary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ entries: window.foodJournalEntries })
        });

        if (!response.ok) {
          throw new Error("Failed to fetch summary.");
        }

        const data = await response.json();
        const summary = data.summary;

        const container = document.getElementById("aiSummaryContainer");
        const text = document.getElementById("aiSummaryText");
        text.textContent = summary;
        container.classList.remove("hidden");
        container.scrollIntoView({ behavior: "smooth" });
      } catch (err) {
        alert("Error generating summary: " + err.message);
      } finally {
        hideLoader();
      }
    });
  }


  
  function showLoader() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('hidden');
  }

  function hideLoader() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('hidden');
  }

  // Toggle form
  const toggleButton = document.getElementById('toggleFormButton');
  const formDiv = document.getElementById('entryForm');
  if (toggleButton && formDiv) {
    toggleButton.addEventListener('click', () => {
      formDiv.classList.toggle('hidden');
    });
  }

  // Default date to today
  const dateInput = document.getElementById('dateLogged');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
  }


  // Upload CSV
  const uploadInput = document.getElementById('uploadCsvInput');
  if (uploadInput) {
    uploadInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      showLoader();

      const text = await file.text();
      const rows = text.trim().split("\n").map(line => line.split(",").map(cell => cell.replace(/"/g, "")));
      const dataRows = rows.slice(1);

      for (const row of dataRows) {
        const payload = {
          date_logged: row[0],
          meal_type: row[1],
          food_name: row[2],
          servings: parseInt(row[3]),
          serving_unit: row[4],
          calories: parseInt(row[5]),
          protein: parseFloat(row[6]),
          carbs: parseFloat(row[7]),
          fat: parseFloat(row[8]),
          mood: row[9],
          notes: row[10]
        };

        await fetch("/food-journal", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams(payload)
        });
      }

      alert("CSV upload complete!");
      hideLoader();
      location.reload();
    });
  }

  // Delete Selected
  const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
  if (deleteSelectedBtn) {
    deleteSelectedBtn.addEventListener('click', async () => {
      const idsToDelete = Array.from(document.querySelectorAll('.entryCheckbox'))
        .filter(cb => cb.checked)
        .map(cb => cb.dataset.id);

      if (idsToDelete.length === 0) {
        alert("No entries selected.");
        return;
      }

      if (!confirm(`Are you sure you want to delete ${idsToDelete.length} entries? This action cannot be undone.`)) return;

      showLoader();

      for (const id of idsToDelete) {
        await fetch(`/api/food_journal/${id}`, {
          method: "DELETE"
        });
      }

      hideLoader();
      location.reload();
    });
  }

  // Delete All
  const deleteAllBtn = document.getElementById('deleteAllBtn');
  if (deleteAllBtn) {
    deleteAllBtn.addEventListener('click', async () => {
      if (!confirm("⚠️ Are you absolutely sure you want to delete ALL entries? This cannot be undone.")) return;

      showLoader();

      await fetch(`/api/food_journal`, {
        method: "DELETE"
      });

      hideLoader();
      location.reload();
    });
  }

  // Select All checkbox
  const selectAllCheckbox = document.getElementById('selectAll');
  const entryCheckboxes = document.querySelectorAll('.entryCheckbox');

  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', () => {
      entryCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
      });
    });
  }
});

// CSV generator
function generateCsv(entries, filename) {
  const rows = [
    ["Date", "Meal Type", "Food", "Servings", "Serving Unit", "Calories", "Protein", "Carbs", "Fat", "Mood", "Notes"],
    ...entries.map(entry => [
      entry.date_logged,
      entry.meal_type,
      entry.food_name,
      entry.servings,
      entry.serving_unit,
      entry.calories,
      entry.protein,
      entry.carbs,
      entry.fat,
      entry.mood || "",
      entry.notes || ""
    ])
  ];

  const csvContent = "data:text/csv;charset=utf-8,"
    + rows.map(e => e.map(v => `"${v}"`).join(",")).join("\n");

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// AI Summery of Food Journal and nutritional gaps
const aiSummaryBtn = document.getElementById('aiSummaryBtn');
if (aiSummaryBtn) {
  aiSummaryBtn.addEventListener('click', () => {
    alert("AI Summary coming soon!");
  });
}

// AI Meal Plans buttons
const aiMealPlansBtn = document.getElementById('aiMealPlansBtn');
if (aiMealPlansBtn) {
  aiMealPlansBtn.addEventListener('click', () => {
    alert("AI Meal Plans coming soon!");
  });
}
