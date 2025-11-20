import { useRef, useState } from "react";
import "./App.css";
import {
  enhanceImage,
  detectImage,
  trackImage,
  countLine,
  processVideo,
} from "./services/api";
import type { ProcessMode, EnhancementKind, ProcessingResult } from "./types";

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewURL, setPreviewURL] = useState<string | null>(null);
  const [processMode, setProcessMode] = useState<ProcessMode>("");
  const [enhancementKind, setEnhancementKind] = useState<EnhancementKind>("CLAHE");
  const [brightness, setBrightness] = useState<number>(0);
  const [contrast, setContrast] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessingResult | null>(null);

  const openFileDialog = () => fileInputRef.current?.click();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewURL(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError("Please select a file first");
      return;
    }

    if (!processMode) {
      setError("Please select a processing mode");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const isVideo = selectedFile.type.startsWith("video/");

      if (isVideo) {
        // Process video
        const options: any = {
          track: processMode === "tracking" || processMode === "detect" || processMode.startsWith("counter"),
          count_mode: "none",
        };

        if (processMode === "enhancement") {
          options.enhance = true;
          options.enhancement_kind = enhancementKind;
        }

        if (processMode === "counter-line") {
          options.count_mode = "line";
        }

        const response = await processVideo(selectedFile, options);
        setResult({
          video: response.video,
          video_url: response.video_url,
          frames_processed: response.frames_processed,
          count_in: response.count_in,
          count_out: response.count_out,
        });
      } else {
        // Process image
        let response;

        switch (processMode) {
          case "enhancement":
            response = await enhanceImage(selectedFile, enhancementKind, brightness, contrast);
            setResult({ image: response.image });
            break;

          case "detect":
            response = await detectImage(selectedFile);
            setResult({
              image: response.image,
              detections: response.detections,
            });
            break;

          case "tracking":
            response = await trackImage(selectedFile);
            setResult({
              image: response.image,
              num_detections: response.num_detections,
            });
            break;

          case "counter-line":
            response = await countLine(selectedFile);
            setResult({
              image: response.image,
              count_in: response.count_in,
              count_out: response.count_out,
            });
            break;

          default:
            throw new Error("Invalid processing mode");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
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

        <select
          className="dropdown"
          value={processMode}
          onChange={(e) => setProcessMode(e.target.value as ProcessMode)}
        >
          <option value="">Select Mode</option>
          <option value="enhancement">Enhancement</option>
          <option value="detect">Detect</option>
          <option value="tracking">Tracking</option>
          <option value="counter-line">Counter (Line)</option>
        </select>

        {processMode === "enhancement" && (
          <div className="options-panel">
            <select
              className="dropdown"
              value={enhancementKind}
              onChange={(e) => setEnhancementKind(e.target.value as EnhancementKind)}
            >
              <option value="CLAHE">CLAHE</option>
              <option value="Histogram">Histogram</option>
              <option value="Gamma">Gamma</option>
              <option value="Bilateral">Bilateral</option>
            </select>

            <label>
              Brightness: {brightness}
              <input
                type="range"
                min="-100"
                max="100"
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
              />
            </label>

            <label>
              Contrast: {contrast}
              <input
                type="range"
                min="-100"
                max="100"
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
              />
            </label>
          </div>
        )}

        <button className="submit-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? "Processing..." : "Submit File"}
        </button>

        {error && <div className="error-message">{error}</div>}
      </div>

      {/* RIGHT PANEL */}
      <div className="right-panel">
        <h2>Output Modelnya</h2>

        {loading && <div className="loading">Processing your file...</div>}

        {result && (
          <div className="result-container">
            {result.image && (
              <img src={result.image} alt="Result" className="result-media" />
            )}

            {(result.video || result.video_url) && (
              <video
                src={result.video_url ? `http://localhost:5000${result.video_url}` : result.video}
                controls
                className="result-media"
              />
            )}

            <div className="result-info">
              {result.detections && (
                <div>
                  <h3>Detections: {result.detections.length}</h3>
                  <ul>
                    {result.detections.map((det, idx) => (
                      <li key={idx}>
                        {det.label} - {(det.confidence * 100).toFixed(2)}%
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.num_detections !== undefined && (
                <p>Number of Detections: {result.num_detections}</p>
              )}

              {result.count_in !== undefined && (
                <p>Count In: {result.count_in}</p>
              )}

              {result.count_out !== undefined && (
                <p>Count Out: {result.count_out}</p>
              )}

              {result.frames_processed !== undefined && (
                <p>Frames Processed: {result.frames_processed}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
