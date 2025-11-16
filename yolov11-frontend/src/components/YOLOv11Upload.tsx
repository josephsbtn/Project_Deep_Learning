import React, { useState } from "react";

export default function YOLOv11Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelType, setModelType] = useState<string>("enhancement");
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [outputUrl, setOutputUrl] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Create preview URL for images and videos
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setOutputUrl(""); // Reset output when new file is selected
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      alert("Please upload a file first!");
      return;
    }

    setIsProcessing(true);

    // TODO: Replace with actual API call to backend
    // Example:
    // const formData = new FormData();
    // formData.append("file", selectedFile);
    // formData.append("model_type", modelType);
    //
    // const response = await fetch("http://localhost:8000/api/process", {
    //   method: "POST",
    //   body: formData,
    // });
    // const result = await response.json();
    // setOutputUrl(result.output_url);

    // Simulate processing
    setTimeout(() => {
      setOutputUrl(previewUrl); // For demo, use the same image
      setIsProcessing(false);
    }, 2000);
  };

  const isVideo = selectedFile?.type.startsWith("video/");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
      {/* Left Panel - Upload & Controls */}
      <div className="lg:col-span-1 flex flex-col space-y-4">
        {/* Upload Area */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-white hover:border-blue-400 transition-colors flex-1 flex flex-col items-center justify-center">
          <input
            type="file"
            id="file-upload"
            accept="image/jpeg,image/png,image/jpg,video/mp4,video/mov"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center"
          >
            <svg
              className="w-16 h-16 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
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
            <p className="text-sm text-gray-500">
              (jpg, png, jpeg, mp4, mov)
            </p>
          </label>

          {selectedFile && (
            <div className="mt-4 text-sm text-green-600 font-medium">
              ✓ {selectedFile.name}
            </div>
          )}
        </div>

        {/* Dropdown - Model Type */}
        <div className="border-2 border-gray-300 rounded-lg p-4 bg-white">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model Type:
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          >
            <option value="enhancement">Enhancement</option>
            <option value="tracking">Tracking</option>
            <option value="counter">Counter</option>
          </select>
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={!selectedFile || isProcessing}
          className={`w-full py-3 px-6 rounded-lg font-medium text-white transition-colors ${
            !selectedFile || isProcessing
              ? "bg-gray-300 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
          }`}
        >
          {isProcessing ? "Processing..." : "Submit File"}
        </button>
      </div>

      {/* Right Panel - Output */}
      <div className="lg:col-span-2 border-2 border-gray-300 rounded-lg bg-white overflow-hidden">
        <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
          <h3 className="text-lg font-semibold text-gray-700">Output Modelnya</h3>
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
                  className="max-w-full max-h-full mx-auto"
                >
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
