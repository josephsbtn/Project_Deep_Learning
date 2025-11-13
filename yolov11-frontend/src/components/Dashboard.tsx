import React from "react";
import FileManager from "./FileManager";
import ImageEnhancement from "./ImageEnhancement";
import ObjectRegion from "./ObjectRegion";
import Tracking from "./Tracking";
import ReportExport from "./ReportExport";

/*
 Dashboard comp arranges the modules:
 - FileManager: upload sample image/video, links (folder/ppt/youtube)
 - ImageEnhancement: client-side enhancement preview (before/after)
 - ObjectRegion: draw/select 1 region on image
 - Tracking: run tracking (calls backend or simulate)
 - ReportExport: export CSV excel-like report before/after
*/
export default function Dashboard(props) {
  return (
    <div className="space-y-6">
      <section className="bg-white p-5 rounded shadow">
        <h2 className="text-lg font-semibold mb-3">1. Project Links & Files</h2>
        <FileManager {...props} />
      </section>

      <section className="bg-white p-5 rounded shadow">
        <h2 className="text-lg font-semibold mb-3">2. Image Enhancement</h2>
        <ImageEnhancement />
      </section>

      <section className="bg-white p-5 rounded shadow">
        <h2 className="text-lg font-semibold mb-3">3. Object Region (pilih 1)</h2>
        <ObjectRegion />
      </section>

      <section className="bg-white p-5 rounded shadow">
        <h2 className="text-lg font-semibold mb-3">4. Tracking (dipilih dari: counting / tracking)</h2>
        <Tracking />
      </section>

      <section className="bg-white p-5 rounded shadow">
        <h2 className="text-lg font-semibold mb-3">5. Laporan (Excel / CSV)</h2>
        <ReportExport />
      </section>

      <section className="bg-white p-5 rounded shadow text-sm text-gray-600">
        <h3 className="font-semibold">Catatan teknis (GUI & stack):</h3>
        <ul className="list-disc ml-5 mt-2">
          <li>Frontend: <strong>React (Vite)</strong> + <strong>Tailwind CSS</strong>.</li>
          <li>Backend (disarankan): Python (FastAPI/Flask) atau Node.js (Express). Model YOLOv11 sebaiknya di-run di backend GPU server.</li>
          <li>Endpoint API contoh:
            <code className="bg-gray-100 px-1 ml-2">POST /api/enhance</code>,
            <code className="bg-gray-100 px-1 ml-2">POST /api/run-yolov11</code>,
            <code className="bg-gray-100 px-1 ml-2">POST /api/track</code>.
          </li>
          <li>Pilih tracking untuk feature tracking (multi-object tracker) — frontend menampilkan bounding boxes dan id.</li>
        </ul>
      </section>
    </div>
  );
}
