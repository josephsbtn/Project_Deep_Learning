import React from "react";

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto p-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">YOLOv11 — Project Dashboard</h1>
          <p className="text-sm text-gray-500">Frontend: React + Tailwind (demo untuk GUI)</p>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-600">Pilihan: Tracking (dipilih)</div>
          <div className="text-xs text-gray-600">Object region: 1 region</div>
        </div>
      </div>
    </header>
  );
}
