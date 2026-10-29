(() => {
  const quote = value => '"' + String(value ?? "").replace(/"/g, '""') + '"';

  function downloadCsv(filename, rows) {
    if (!rows || !rows.length) return;
    const csv = "\uFEFF" + rows.map(row => row.map(quote).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], {type: "text/csv;charset=utf-8"}));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "nba-data.csv";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  window.downloadNbaCsv = downloadCsv;

  document.addEventListener("click", event => {
    const button = event.target.closest("[data-download-table], [data-download-chart]");
    if (!button) return;

    if (button.dataset.downloadTable) {
      const table = document.getElementById(button.dataset.downloadTable);
      if (!table) return;
      const rows = Array.from(table.querySelectorAll("tr")).map(row =>
        Array.from(row.querySelectorAll("th, td")).map(cell => cell.textContent.trim())
      );
      downloadCsv(button.dataset.filename, rows);
      return;
    }

    const chart = document.getElementById(button.dataset.downloadChart);
    if (!chart) return;
    const headers = JSON.parse(chart.dataset.csvHeaders || "[]");
    const rows = Array.from(chart.querySelectorAll("[data-csv-row]")).map(bar =>
      JSON.parse(bar.dataset.csvRow)
    );
    downloadCsv(button.dataset.filename, [headers, ...rows]);
  });
})();