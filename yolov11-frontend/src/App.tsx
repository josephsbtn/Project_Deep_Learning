import { useRef, useState } from "react";
import "./App.css";

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewURL, setPreviewURL] = useState<string | null>(null);

  const openFileDialog = () => fileInputRef.current?.click();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewURL(URL.createObjectURL(file));
    }
  };

  return (
    <div className="layout">

      {/* LEFT PANEL */}
      <div className="left-panel">

        <div className="upload-box" onClick={openFileDialog}>
          {previewURL ? (
            selectedFile?.type.startsWith("video/") ? (
              <video className="preview-media" src={previewURL} controls />
            ) : (
              <img className="preview-media" src={previewURL} alt="preview" />
            )
          ) : (
            <>
              <p className="upload-title">Upload File</p>
              <p className="upload-sub">(jpg, png, jpeg, mp4, mov)</p>
            </>
          )}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept="image/*,video/*"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />

        <select className="dropdown">
          <option value="">Enhancement</option>
          <option value="tracking">Tracking</option>
          <option value="counter">Counter</option>
        </select>

        <button className="submit-btn">Submit File</button>

      </div>

      {/* RIGHT PANEL */}
      <div className="right-panel">
        <h2>Output Modelnya</h2>
      </div>

    </div>
  );
}

export default App;
