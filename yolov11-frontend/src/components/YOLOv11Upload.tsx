import React, { useState } from "react";

type ModelType =
  | "enhancement"
  | "detect"
  | "track"
  | "count-line"
  | "count-polygon";
type EnhancementKind = "CLAHE" | "HE" | "BC" | "CS";

interface ProcessResult {
  image?: string;
  video?: string;
  detections?: any[];
  count_in?: number;
  count_out?: number;
  count?: number;
  frames_processed?: number;
  num_detections?: number;
}

export default function YOLOv11Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelType, setModelType] = useState<ModelType>("enhancement");
  const [enhancementKind, setEnhancementKind] =
    useState<EnhancementKind>("CLAHE");
  const [brightness, setBrightness] = useState<number>(0);
  const [contrast, setContrast] = useState<number>(0);
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [outputUrl, setOutputUrl] = useState<string>("");
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const API_BASE = "http://localhost:5000";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setOutputUrl("");
      setResult(null);
      setError("");
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      alert("Please upload a file first!");
      return;
    }

    setIsProcessing(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      let endpoint = "";
      let response: Response;

      const isVideo = selectedFile.type.startsWith("video/");

      // Image Processing
      if (!isVideo) {
        switch (modelType) {
          case "enhancement":
            endpoint = "/enhance-image";
            formData.append("kind", enhancementKind);
            formData.append("brightness", brightness.toString());
            formData.append("contrast", contrast.toString());
            break;

          case "detect":
            endpoint = "/detect";
            break;

          case "track":
            endpoint = "/track";
            formData.append("tracker", "bytetrack.yaml");
            break;

          case "count-line":
            endpoint = "/count-line";
            formData.append("tracker", "bytetrack.yaml");
            break;

          case "count-polygon":
            // Note: Polygon requires polygon_id from /create-polygon endpoint
            alert("Polygon counting requires polygon setup first");
            setIsProcessing(false);
            return;
        }

        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          body: formData,
        });
      }
      // Video Processing
      else {
        endpoint = "/process-video";
        formData.append("track", modelType === "track" ? "true" : "false");

        if (modelType === "enhancement") {
          formData.append("enhance", "true");
          formData.append("enhancement_kind", enhancementKind);
        }

        if (modelType === "count-line") {
          formData.append("track", "true");
          formData.append("count_mode", "line");
        }

        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          body: formData,
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ProcessResult = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setResult(data);

      // Set output URL from base64
      if (data.image) {
        setOutputUrl(data.image);
      } else if (data.video) {
        setOutputUrl(data.video);
      }
    } catch (err) {
      console.error("Error processing file:", err);
      setError(err instanceof Error ? err.message : "Failed to process file");
    } finally {
      setIsProcessing(false);
    }
  };

  const isVideo = selectedFile?.type.startsWith("video/");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
      {/* Left Panel - Upload & Controls */}
      <div className="lg:col-span-1 flex flex-col space-y-4 overflow-y-auto">
        {/* Upload Area */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-white hover:border-blue-400 transition-colors flex-shrink-0">
          <input
            type="file"
            id="file-upload"
            accept="image/jpeg,image/png,image/jpg,video/mp4,video/mov"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center">
            <svg
              className="w-16 h-16 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-lg font-medium text-gray-700 mb-2">
              Upload File
            </p>
            <p className="text-sm text-gray-500">(jpg, png, jpeg, mp4, mov)</p>
          </label>

          {selectedFile && (
            <div className="mt-4 text-sm text-green-600 font-medium">
              ✓ {selectedFile.name}
            </div>
          )}
        </div>

        {/* Model Type Selection */}
        <div className="border-2 border-gray-300 rounded-lg p-4 bg-white">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model Type:
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value as ModelType)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none">
            <option value="enhancement">Enhancement</option>
            <option value="detect">Detection</option>
            <option value="track">Tracking</option>
            <option value="count-line">Line Counting</option>
            <option value="count-polygon">Polygon Counting</option>
          </select>
        </div>

        {/* Enhancement Options (only show for enhancement mode) */}
        {modelType === "enhancement" && (
          <div className="border-2 border-gray-300 rounded-lg p-4 bg-white space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enhancement Method:
              </label>
              <select
                value={enhancementKind}
                onChange={(e) =>
                  setEnhancementKind(e.target.value as EnhancementKind)
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none">
                <option value="CLAHE">CLAHE</option>
                <option value="HE">Histogram Equalization</option>
                <option value="BC">Brightness/Contrast</option>
                <option value="CS">Contrast Stretching</option>
              </select>
            </div>

            {enhancementKind === "BC" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brightness: {brightness}
                  </label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={brightness}
                    onChange={(e) => setBrightness(Number(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contrast: {contrast}
                  </label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={contrast}
                    onChange={(e) => setContrast(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
              </>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={!selectedFile || isProcessing}
          className={`w-full py-3 px-6 rounded-lg font-medium text-white transition-colors ${
            !selectedFile || isProcessing
              ? "bg-gray-300 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
          }`}>
          {isProcessing ? "Processing..." : "Submit File"}
        </button>

        {/* Error Message */}
        {error && (
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <p className="text-sm text-red-600">❌ {error}</p>
          </div>
        )}

        {/* Results Info */}
        {result && (
          <div className="border-2 border-green-300 rounded-lg p-4 bg-green-50">
            <h4 className="text-sm font-semibold text-green-800 mb-2">
              Results:
            </h4>
            <div className="text-sm text-green-700 space-y-1">
              {result.num_detections !== undefined && (
                <p>✓ Detections: {result.num_detections}</p>
              )}
              {result.detections && (
                <p>✓ Objects: {result.detections.length}</p>
              )}
              {result.count_in !== undefined && (
                <p>✓ Count In: {result.count_in}</p>
              )}
              {result.count_out !== undefined && (
                <p>✓ Count Out: {result.count_out}</p>
              )}
              {result.count !== undefined && <p>✓ Count: {result.count}</p>}
              {result.frames_processed !== undefined && (
                <p>✓ Frames: {result.frames_processed}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Panel - Output */}
      <div className="lg:col-span-2 border-2 border-gray-300 rounded-lg bg-white overflow-hidden">
        <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
          <h3 className="text-lg font-semibold text-gray-700">Output Model</h3>
        </div>

        <div className="h-[calc(100%-48px)] flex items-center justify-center p-4">
          {isProcessing ? (
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Processing your file...</p>
            </div>
          ) : outputUrl ? (
            <div className="w-full h-full">
              {isVideo ? (
                <video
                  src={outputUrl}
                  controls
                  className="max-w-full max-h-full mx-auto">
                  Your browser does not support the video tag.
                </video>
              ) : (
                <img
                  src={outputUrl}
                  alt="Output"
                  className="max-w-full max-h-full object-contain mx-auto"
                />
              )}
            </div>
          ) : (
            <p className="text-gray-400 text-lg">
              Upload and submit a file to see the output here
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
