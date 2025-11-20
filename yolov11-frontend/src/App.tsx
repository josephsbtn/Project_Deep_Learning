import { useRef, useState } from "react";
import "./App.css";
import { detect, track, count, createPolygon } from "./services/api";
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

  // Polygon state for counter mode
  const [polygonPoints, setPolygonPoints] = useState<string>("100,100\n200,100\n200,200\n100,200");
  const [polygonId, setPolygonId] = useState<string | null>(null);
  const [polygonCreating, setPolygonCreating] = useState<boolean>(false);

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

  const handleCreatePolygon = async () => {
    try {
      setPolygonCreating(true);
      setError(null);

      // Parse polygon points from textarea
      const lines = polygonPoints.trim().split("\n");
      const points = lines.map(line => {
        const [x, y] = line.split(",").map(n => parseInt(n.trim()));
        return [x, y];
      });

      if (points.length < 3) {
        setError("Polygon needs at least 3 points");
        return;
      }

      const response = await createPolygon(points);
      setPolygonId(response.polygon_id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create polygon");
    } finally {
      setPolygonCreating(false);
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
      const enhanceOptions = processMode === "enhancement" ? {
        enhance: true,
        enhancement_kind: enhancementKind,
        brightness: brightness,
        contrast: contrast,
      } : undefined;

      switch (processMode) {
        case "enhancement":
        case "detect": {
          const response = await detect(selectedFile, enhanceOptions);
          setResult({
            image: response.image,
            video_url: response.video_url,
            detections: response.detections,
            frames_processed: response.frames_processed,
          });
          break;
        }

        case "tracking": {
          const response = await track(selectedFile, enhanceOptions);
          setResult({
            image: response.image,
            video_url: response.video_url,
            num_detections: response.num_detections,
            frames_processed: response.frames_processed,
          });
          break;
        }

        case "counter": {
          if (!polygonId) {
            setError("Please create a polygon first");
            setLoading(false);
            return;
          }
          const response = await count(selectedFile, polygonId, enhanceOptions);
          setResult({
            image: response.image,
            video_url: response.video_url,
            count: response.count,
            frames_processed: response.frames_processed,
          });
          break;
        }

        default:
          throw new Error("Invalid processing mode");
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
          <option value="counter">Object Counter</option>
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

        {processMode === "counter" && (
          <div className="options-panel">
            <label>
              Polygon Coordinates (x,y per line):
              <textarea
                className="polygon-input"
                value={polygonPoints}
                onChange={(e) => setPolygonPoints(e.target.value)}
                rows={5}
                placeholder={"100,100\n200,100\n200,200\n100,200"}
              />
            </label>
            <button
              className="create-polygon-btn"
              onClick={handleCreatePolygon}
              disabled={polygonCreating}
            >
              {polygonCreating ? "Creating..." : "Create Polygon"}
            </button>
            {polygonId && (
              <p className="polygon-status">Polygon ID: {polygonId}</p>
            )}
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

            {result.video_url && (
              <video
                src={`http://localhost:5000${result.video_url}`}
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

              {result.count !== undefined && (
                <p>Count: {result.count}</p>
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
