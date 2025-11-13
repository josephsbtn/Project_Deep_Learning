import React, { useRef, useState } from "react";

/*
 Simple client-side enhancement demo:
 - load image
 - adjust brightness & contrast sliders
 - show before/after side-by-side on canvas
 - export "before" and "after" summary metrics to parent (for CSV).
*/
export default function ImageEnhancement() {
  const [src, setSrc] = useState(null);
  const [brightness, setBrightness] = useState(0);
  const [contrast, setContrast] = useState(0);
  const beforeRef = useRef();
  const afterRef = useRef();

  function onFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    setSrc(url);
  }

  function applyEnhancement(imgEl, canvas, b, c) {
    const w = imgEl.naturalWidth, h = imgEl.naturalHeight;
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(imgEl, 0, 0);
    const img = ctx.getImageData(0,0,w,h);
    const data = img.data;
    const bFactor = b; // -100 .. +100
    const cFactor = (c/100)+1; // -100..+100 -> scale
    for (let i=0;i<data.length;i+=4){
      for (let j=0;j<3;j++){
        let val = data[i+j];
        val = (val - 128) * cFactor + 128 + bFactor;
        data[i+j] = Math.max(0,Math.min(255, val));
      }
    }
    ctx.putImageData(img,0,0);
  }

  function drawBoth() {
    if (!src) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      // before
      const beforeCanvas = beforeRef.current;
      beforeCanvas.width = img.naturalWidth;
      beforeCanvas.height = img.naturalHeight;
      beforeCanvas.getContext("2d").drawImage(img,0,0);

      // after
      const afterCanvas = afterRef.current;
      applyEnhancement(img, afterCanvas, Number(brightness), Number(contrast));
    };
    img.src = src;
  }

  // update whenever sliders change or src changes
  React.useEffect(()=> { drawBoth(); }, [src, brightness, contrast]);

  return (
    <div className="space-y-4">
      <div>
        <input type="file" accept="image/*" onChange={onFile} />
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <p className="text-sm font-medium">Before</p>
          <div className="overflow-auto border rounded p-2 bg-gray-50">
            <canvas ref={beforeRef} className="max-w-full" />
          </div>
        </div>

        <div className="flex-1">
          <p className="text-sm font-medium">After (enhanced)</p>
          <div className="overflow-auto border rounded p-2 bg-gray-50">
            <canvas ref={afterRef} className="max-w-full" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm">Brightness (-100..100): {brightness}</label>
          <input type="range" min="-100" max="100" value={brightness}
                 onChange={e=>setBrightness(e.target.value)} className="w-full" />
        </div>
        <div>
          <label className="text-sm">Contrast (-100..100): {contrast}</label>
          <input type="range" min="-100" max="100" value={contrast}
                 onChange={e=>setContrast(e.target.value)} className="w-full" />
        </div>
      </div>

      <p className="text-xs text-gray-500">
        Catatan: Ini demo enhancement client-side sederhana (contrast/brightness). Untuk enhancement
        berbasis model/algoritma lanjutan (ex: DNN denoise/superres), jalankan di backend dan panggil API.
      </p>
    </div>
  );
}