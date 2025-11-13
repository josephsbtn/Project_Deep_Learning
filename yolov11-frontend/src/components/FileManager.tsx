import React, { useState } from "react";

export default function FileManager({ projectLink, setProjectLink, pptLink, setPptLink, youtubeLink, setYoutubeLink }) {
  const [sampleImage, setSampleImage] = useState(null);
  const [sampleVideo, setSampleVideo] = useState(null);

  function onImageChange(e) {
    const f = e.target.files[0];
    if (f) setSampleImage(URL.createObjectURL(f));
  }
  function onVideoChange(e) {
    const f = e.target.files[0];
    if (f) setSampleVideo(URL.createObjectURL(f));
  }

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium">Link folder kelompok (Google Drive / OneDrive)</label>
        <input value={projectLink} onChange={(e)=>setProjectLink(e.target.value)} placeholder="https://drive.google.com/..." className="mt-1 w-full p-2 border rounded" />
        <p className="text-xs text-gray-500 mt-1">Masukkan link folder proyek kalian.</p>

        <label className="block text-sm font-medium mt-4">Upload contoh image</label>
        <input type="file" accept="image/*" onChange={onImageChange} className="mt-1" />
        {sampleImage && <img src={sampleImage} alt="sample" className="mt-3 max-h-48 rounded shadow" />}

        <label className="block text-sm font-medium mt-4">Upload contoh video</label>
        <input type="file" accept="video/*" onChange={onVideoChange} className="mt-1" />
        {sampleVideo && <video src={sampleVideo} controls className="mt-3 max-h-48 rounded shadow" />}
      </div>

      <div>
        <label className="block text-sm font-medium">Link PPT akhir (upload ke Drive / link)</label>
        <input value={pptLink} onChange={(e)=>setPptLink(e.target.value)} placeholder="https://..." className="mt-1 w-full p-2 border rounded" />

        <label className="block text-sm font-medium mt-4">Link video YouTube (project akhir)</label>
        <input value={youtubeLink} onChange={(e)=>setYoutubeLink(e.target.value)} placeholder="https://youtu.be/..." className="mt-1 w-full p-2 border rounded" />
        {youtubeLink && (
          <div className="mt-3">
            <p className="text-sm">Preview YouTube:</p>
            <div className="mt-2 aspect-video">
              <iframe
                title="youtube-preview"
                src={sanitizeYoutube(youtubeLink)}
                className="w-full h-48 rounded"
                frameBorder="0"
                allowFullScreen
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function sanitizeYoutube(url) {
  // basic transform to embed url for youtube links
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtu.be")) {
      const id = u.pathname.slice(1);
      return `https://www.youtube.com/embed/${id}`;
    } else if (u.hostname.includes("youtube.com")) {
      const q = new URLSearchParams(u.search);
      const id = q.get("v");
      return id ? `https://www.youtube.com/embed/${id}` : url;
    }
    return url;
  } catch (err) {
    return url;
  }
}