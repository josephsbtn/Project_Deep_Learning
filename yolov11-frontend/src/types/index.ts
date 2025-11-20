// Types for State Management

export type ProcessMode = "enhancement" | "detect" | "tracking" | "counter" | "";

export type EnhancementKind = "CLAHE" | "Histogram" | "Gamma" | "Bilateral";

export type CountMode = "none" | "line" | "polygon";

export interface Detection {
  box: number[];
  class_id: number;
  confidence: number;
  label: string;
}

export interface ProcessingOptions {
  mode: ProcessMode;
  enhancementKind?: EnhancementKind;
  brightness?: number;
  contrast?: number;
  tracker?: string;
  countMode?: CountMode;
  polygonId?: string;
}

export interface ProcessingResult {
  image?: string;
  video?: string;
  video_url?: string;
  detections?: Detection[];
  count_in?: number;
  count_out?: number;
  count?: number;
  num_detections?: number;
  frames_processed?: number;
}
