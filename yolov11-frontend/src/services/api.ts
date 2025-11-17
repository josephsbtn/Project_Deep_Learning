// API Service for YOLOv11 Backend

const API_BASE_URL = "http://localhost:5000";

export interface EnhanceImageResponse {
  image: string;
  kind: string;
}

export interface Detection {
  box: number[];
  class_id: number;
  confidence: number;
  label: string;
}

export interface DetectResponse {
  image: string;
  detections: Detection[];
}

export interface TrackResponse {
  image: string;
  num_detections: number;
}

export interface CountLineResponse {
  image: string;
  count_in: number;
  count_out: number;
}

export interface CountPolygonResponse {
  image: string;
  count_in: number;
}

export interface ProcessVideoResponse {
  video?: string;
  video_url?: string;
  frames_processed: number;
  count_in?: number;
  count_out?: number;
  count?: number;
}

export interface CreatePolygonResponse {
  polygon_id: string;
}

// Enhancement API
export const enhanceImage = async (
  file: File,
  kind: string = "CLAHE",
  brightness: number = 0,
  contrast: number = 0
): Promise<EnhanceImageResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("kind", kind);
  formData.append("brightness", brightness.toString());
  formData.append("contrast", contrast.toString());

  const response = await fetch(`${API_BASE_URL}/enhance-image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to enhance image");
  }

  return response.json();
};

// Detect API
export const detectImage = async (file: File): Promise<DetectResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/detect`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to detect objects");
  }

  return response.json();
};

// Track API
export const trackImage = async (
  file: File,
  tracker: string = "bytetrack.yaml"
): Promise<TrackResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tracker", tracker);

  const response = await fetch(`${API_BASE_URL}/track`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to track objects");
  }

  return response.json();
};

// Count Line API
export const countLine = async (
  file: File,
  tracker: string = "bytetrack.yaml"
): Promise<CountLineResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tracker", tracker);

  const response = await fetch(`${API_BASE_URL}/count-line`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to count with line");
  }

  return response.json();
};

// Create Polygon API
export const createPolygon = async (
  points: number[][]
): Promise<CreatePolygonResponse> => {
  const response = await fetch(`${API_BASE_URL}/create-polygon`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ points }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to create polygon");
  }

  return response.json();
};

// Count Polygon API
export const countPolygon = async (
  polygonId: string,
  file: File,
  tracker: string = "bytetrack.yaml"
): Promise<CountPolygonResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tracker", tracker);

  const response = await fetch(
    `${API_BASE_URL}/count-polygon/${polygonId}`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to count with polygon");
  }

  return response.json();
};

// Process Video API
export const processVideo = async (
  file: File,
  options: {
    enhance?: boolean;
    enhancement_kind?: string;
    track?: boolean;
    count_mode?: "none" | "line" | "polygon";
    polygon_id?: string;
  } = {}
): Promise<ProcessVideoResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("enhance", options.enhance ? "true" : "false");
  formData.append("enhancement_kind", options.enhancement_kind || "CLAHE");
  formData.append("track", options.track ? "true" : "false");
  formData.append("count_mode", options.count_mode || "none");

  if (options.polygon_id) {
    formData.append("polygon_id", options.polygon_id);
  }

  const response = await fetch(`${API_BASE_URL}/process-video`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to process video");
  }

  return response.json();
};

// List Outputs API
export const listOutputs = async (): Promise<{ files: string[] }> => {
  const response = await fetch(`${API_BASE_URL}/outputs`);

  if (!response.ok) {
    throw new Error("Failed to list outputs");
  }

  return response.json();
};

// Download File API
export const downloadFile = (filename: string): string => {
  return `${API_BASE_URL}/download?filename=${encodeURIComponent(filename)}`;
};
