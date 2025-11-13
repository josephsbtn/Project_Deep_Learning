import React, { useRef, useState, useEffect } from "react";

/*
 Simple rectangle drawing on image to select 1 object region.
 Allows upload and drawing exactly 1 region.
*/
export default function ObjectRegion() {
  const [imgSrc, setImgSrc] = useState(null);
  const canvasRef = useRef();
  const imgRef = useRef();
  const [rect, setRect] = useState(null);
  const [dragging, setDragging] = useState(false);
  const startRef = useRef(null);

  function onFile(e){
    const f = e.target.files[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    setImgSrc(url);
  }

  useEffect(()=> {
    if (!imgSrc) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imgRef.current = img;
      const c = canvasRef.current;
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      const ctx = c.getContext("2d");
      ctx.clearRect(0,0,c.width,c.height);
      ctx.drawImage(img,0,0);
      if (rect) drawRect(ctx, rect);
    };
    img.src = imgSrc;
  }, [imgSrc, rect]);

  function drawRect(ctx, r) {
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;
    ctx.strokeRect(r.x, r.y, r.w, r.h);
  }

  function clientToCanvas(e) {
    const c = canvasRef.current;
    const rectBox = c.getBoundingClientRect();
    const x = Math.round((e.clientX - rectBox.left) * (c.width / rectBox.width));
    const y = Math.round((e.clientY - rectBox.top) * (c.height / rectBox.height));
    return {x,y};
  }

  function onDown(e){
    if (!imgRef.current) return;
    const pos = clientToCanvas(e);
    startRef.current = pos;
    setDragging(true);
  }
  function onMove(e){
    if (!dragging) return;
    const pos = clientToCanvas(e);
    const sx = startRef.current.x, sy = startRef.current.y;
    const w = pos.x - sx, h = pos.y - sy;
    setRect({x: Math.min(sx,pos.x), y: Math.min(sy,pos.y), w: Math.abs(w), h: Math.abs(h)});
    // redraw
    const c = canvasRef.current;
    const ctx = c.getContext("2d");
    ctx.clearRect(0,0,c.width,c.height);
    ctx.drawImage(imgRef.current,0,0);
    if (rect) drawRect(ctx, {x: Math.min(sx,pos.x), y: Math.min(sy,pos.y), w: Math.abs(w), h: Math.abs(h)});
  }
  function onUp(){
    setDragging(false);
    startRef.current = null;
  }

  return (
    <div>
      <div className="mb-3">
        <input type="file" accept="image/*" onChange={onFile} />
      </div>
      <div className="overflow-auto border rounded bg-gray-50">
        {imgSrc ? (
          <canvas
            ref={canvasRef}
            className="max-w-full"
            onMouseDown={onDown}
            onMouseMove={onMove}
            onMouseUp={onUp}
            onMouseLeave={onUp}
            style={{cursor: "crosshair"}}
          />
        ) : (
          <div className="p-8 text-gray-500">Belum ada gambar. Upload gambar untuk pilih region.</div>
        )}
      </div>

      {rect && (
        <div className="mt-3 bg-white border rounded p-3">
          <div>Terpilih 1 region:</div>
          <pre className="text-sm bg-gray-50 p-2 rounded mt-2">
            {JSON.stringify(rect, null, 2)}
          </pre>
          <div className="text-xs text-gray-500 mt-1">Koordinat dalam pixel (canvas asli).</div>
        </div>
      )}
    </div>
  );
}