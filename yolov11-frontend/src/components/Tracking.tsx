import React, { useRef, useState } from "react";

/*
 Tracking component:
 - upload video or image sequence (demo)
 - button "Run Tracking" which in real project should call backend tracking API.
 - For demo: we simulate tracked boxes (random) over video frames.
 - If connected to backend: POST /api/track with file, receive frames + boxes.
*/
export default function Tracking() {
  const [videoUrl, setVideoUrl] = useState(null);
  const videoRef = useRef();
  const [running, setRunning] = useState(false);
  const [simBoxes, setSimBoxes] = useState([]);

  function onVideoChange(e){
    const f = e.target.files[0];
    if (!f) return;
    setVideoUrl(URL.createObjectURL(f));
  }

  function runTrackingSim(){
    // simulate a few tracked boxes (id, bbox)
    setRunning(true);
    const boxes = [
      {id:1, x:50, y:50, w:80, h:120, color: 'red'},
      {id:2, x:200, y:120, w:100, h:90, color: 'blue'}
    ];
    setSimBoxes(boxes);
    // In real app: upload video to backend -> receive tracking results (per-frame)
    setTimeout(()=> setRunning(false), 1000);
  }

  return (
    <div className="space-y-3">
      <div>
        <input type="file" accept="video/*" onChange={onVideoChange} />
      </div>
      <div className="border rounded p-2 bg-gray-50 relative">
        {videoUrl ? (
          <div className="relative">
            <video ref={videoRef} src={videoUrl} controls className="w-full" />
            {/* overlay simulated boxes */}
            <div className="absolute top-2 left-2 pointer-events-none w-full h-full">
              {simBoxes.map(b => (
                <div key={b.id}
                  style={{
                    position:'absolute',
                    left: `${b.x}px`,
                    top: `${b.y}px`,
                    width: `${b.w}px`,
                    height: `${b.h}px`,
                    border: `2px solid ${b.color}`,
                    color: b.color,
                    fontWeight: '600',
                    background: 'rgba(255,255,255,0.0)'
                  }}>
                  <div style={{fontSize:12, background:'rgba(255,255,255,0.6)', padding:'2px'}}>
                    ID:{b.id}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 text-gray-500">Upload video untuk menjalankan tracking.</div>
        )}
      </div>

      <div className="flex gap-2">
        <button onClick={runTrackingSim} className="px-4 py-2 bg-indigo-600 text-white rounded">
          {running ? "Running..." : "Run Tracking (Sim) / Call API"}
        </button>
        <button className="px-4 py-2 border rounded" onClick={()=>setSimBoxes([])}>Clear Boxes</button>
      </div>

      <p className="text-xs text-gray-500">
        Penjelasan: Tracking (dipilih) — modul ini mengharuskan backend yang menjalankan tracker (mis. DeepSORT, ByteTrack) menerima hasil deteksi YOLOv11 per frame dan mengembalikan ID & bounding boxes per frame.
      </p>
    </div>
  );
}