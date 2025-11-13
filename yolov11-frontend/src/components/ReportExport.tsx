import React from "react";

/*
 Exports a CSV "Excel-readable" report for Before/After enhancement.
 For demo, we create a small CSV with metric rows: brightness/contrast + dummy object counts.
*/
export default function ReportExport() {
  function downloadCSV() {
    const rows = [
      ["File","Metric","Before","After"],
      ["image1.jpg","MeanBrightness","120","140"],
      ["image1.jpg","Contrast","1.0","1.2"],
      ["image1.jpg","DetectedObjects","3","4"]
    ];
    const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "report_before_after.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <p className="text-sm">Export laporan Excel (CSV) yang berisi metrik sebelum & sesudah enhancement. File bisa dibuka dengan Excel.</p>
      <div className="mt-3">
        <button onClick={downloadCSV} className="px-4 py-2 bg-green-600 text-white rounded">Download CSV (Excel)</button>
      </div>
    </div>
  );
}
