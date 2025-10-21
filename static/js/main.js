document.addEventListener("DOMContentLoaded", function() {
  // Admin: handle update clicks
  document.querySelectorAll(".update-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = btn.dataset.id;
      const select = document.querySelector(`select[data-id='${id}']`);
      const note = document.querySelector(`.note-input[data-id='${id}']`).value || "";
      const actor = "Admin"; // you can implement admin name input later

      const payload = { id: parseInt(id), status: select.value, actor: actor, note: note };
      try {
        const res = await fetch("/admin/update_status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.ok) {
          // update displayed status cell
          const statusCell = document.getElementById(`status-${id}`);
          if (statusCell) statusCell.textContent = data.new_status;
          // also update detail status label if open
          const label = document.getElementById("status-label");
          if (label && parseInt(id) === parseInt(label.datasetId)) label.textContent = data.new_status;
          alert("Status updated");
        } else {
          alert("Error: " + (data.error || "unknown"));
        }
      } catch (err) {
        console.error(err);
        alert("Network error");
      }
    });
  });

  // Optional: auto-refresh issue status on detail page
  if (document.getElementById("status-label")) {
    const statusLabel = document.getElementById("status-label");
    // store data-id if present
    const pathMatch = window.location.pathname.match(/\/issue\/(\d+)/);
    if (pathMatch) {
      const issueId = pathMatch[1];
      // poll every 20 seconds
      setInterval(async () => {
        try {
          const r = await fetch(`/api/issue_status/${issueId}`);
          if (!r.ok) return;
          const d = await r.json();
          if (d.status && statusLabel.textContent !== d.status) {
            statusLabel.textContent = d.status;
          }
        } catch(e) { /* ignore */ }
      }, 20000);
    }
  }
});
