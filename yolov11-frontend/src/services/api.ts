// API Service for YOLOv11 Backend

const API_BASE_URL = "http://localhost:5000";

// ============================================================================
// RESPONSE TYPES
// ============================================================================

export interface Detection {
  box: number[];
  class_id: number;
  confidence: number;
  label: string;
}

// Detect Response
export interface DetectResponse {
  type: "image" | "video";
  image?: string;
  video_url?: string;
  detections?: Detection[];
  total_detections?: number;
  frames_processed?: number;
  enhancement_applied?: boolean;
}

// Track Response
export interface TrackResponse {
  type: "image" | "video";
  image?: string;
  video_url?: string;
  num_detections?: number;
  frames_processed?: number;
  enhancement_applied?: boolean;
  tracker?: string;
}

// Count Response
export interface CountResponse {
  type: "image" | "video";
  image?: string;
  video_url?: string;
  count_in?: number;
  count_out?: number;
  count?: number;
  frames_processed?: number;
  enhancement_applied?: boolean;
  region_type?: string;
  tracker?: string;
}

// Polygon Response
export interface CreatePolygonResponse {
  polygon_id: string;
  message: string;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Detect objects in image or video
 */
export const detect = async (
  file: File,
  options?: {
    enhance?: boolean;
    enhancement_kind?: string;
    brightness?: number;
    contrast?: number;
  }
): Promise<DetectResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  if (options?.enhance) {
    formData.append("enhance", "true");
    formData.append("enhancement_kind", options.enhancement_kind || "CLAHE");
    formData.append("brightness", String(options.brightness || 0));
    formData.append("contrast", String(options.contrast || 0));
  }

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

/**
 * Track objects in image or video
 */
export const track = async (
  file: File,
  options?: {
    enhance?: boolean;
    enhancement_kind?: string;
    brightness?: number;
    contrast?: number;
    tracker?: string;
  }
): Promise<TrackResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  if (options?.enhance) {
    formData.append("enhance", "true");
    formData.append("enhancement_kind", options.enhancement_kind || "CLAHE");
    formData.append("brightness", String(options.brightness || 0));
    formData.append("contrast", String(options.contrast || 0));
  }

  if (options?.tracker) {
    formData.append("tracker", options.tracker);
  }

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

/**
 * Count objects crossing line or inside polygon
 */
export const count = async (
  file: File,
  options: {
    region_type: "line" | "polygon";
    polygon_id?: string;
    enhance?: boolean;
    enhancement_kind?: string;
    brightness?: number;
    contrast?: number;
    tracker?: string;
  }
): Promise<CountResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("region_type", options.region_type);

  if (options.polygon_id) {
    formData.append("polygon_id", options.polygon_id);
  }

  if (options.enhance) {
    formData.append("enhance", "true");
    formData.append("enhancement_kind", options.enhancement_kind || "CLAHE");
    formData.append("brightness", String(options.brightness || 0));
    formData.append("contrast", String(options.contrast || 0));
  }

  if (options.tracker) {
    formData.append("tracker", options.tracker);
  }

  const response = await fetch(`${API_BASE_URL}/count`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to count objects");
  }

  return response.json();
};

/**
 * Create a polygon zone for counting
 */
export const createPolygon = async (
  points: number[][]
): Promise<CreatePolygonResponse> => {
  const response = await fetch(`${API_BASE_URL}/polygon/create`, {
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

/**
 * List all polygon zones
 */
export const listPolygons = async (): Promise<{ polygons: string[]; total: number }> => {
  const response = await fetch(`${API_BASE_URL}/polygon/list`);

  if (!response.ok) {
    throw new Error("Failed to list polygons");
  }

  return response.json();
};

/**
 * Delete a polygon zone
 */
export const deletePolygon = async (polygonId: string): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/polygon/delete/${polygonId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to delete polygon");
  }

  return response.json();
};

/**
 * List all output files
 */
export const listOutputs = async (): Promise<{ files: string[]; total: number }> => {
  const response = await fetch(`${API_BASE_URL}/outputs`);

  if (!response.ok) {
    throw new Error("Failed to list outputs");
  }

  return response.json();
};

/**
 * Get video URL for playback
 */
export const getVideoUrl = (filename: string): string => {
  return `${API_BASE_URL}/video/${filename}`;
};

/**
 * Get download URL for a file
 */
export const getDownloadUrl = (filename: string): string => {
  return `${API_BASE_URL}/download/${filename}`;
};

/**
 * Health check
 */
export const healthCheck = async (): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("API is not healthy");
  }

  return response.json();
};
