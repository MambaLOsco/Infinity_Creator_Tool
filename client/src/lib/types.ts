export type JobStatus = "queued" | "processing" | "complete" | "error";
export type SourceType = "upload" | "youtube";

export interface JobRecord {
  id: string;
  status: JobStatus;
  progress: number;
  createdAt: string;
  updatedAt: string;
  sourceType: SourceType;
  language: string;
  presetId?: string;
  input: any;
  logs: string[];
  artifacts: Record<string, string>;
  errorMessage?: string;
}

export interface Preset {
  id: string;
  name: string;
  watermark: string;
  template: string;
}
