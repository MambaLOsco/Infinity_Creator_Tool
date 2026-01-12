import { JobRecord, Preset } from "./types";

const PRESETS_KEY = "infinity_creator_presets";
const ACTIVE_PRESET_KEY = "infinity_creator_active_preset";

export async function createUploadJob(file: File, language: string, presetId?: string) {
  const data = new FormData();
  data.append("file", file);
  data.append("language", language);
  if (presetId) data.append("presetId", presetId);

  const response = await fetch("/api/jobs/upload", {
    method: "POST",
    body: data,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to create job");
  }

  return (await response.json()) as { jobId: string };
}

export async function createYoutubeJob(url: string, language: string, presetId?: string) {
  const response = await fetch("/api/jobs/youtube", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, language, presetId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to create job");
  }

  return (await response.json()) as { jobId: string };
}

export async function fetchJobs() {
  const response = await fetch("/api/jobs");
  if (!response.ok) throw new Error("Failed to fetch jobs");
  return (await response.json()) as JobRecord[];
}

export async function fetchJob(jobId: string) {
  const response = await fetch(`/api/jobs/${jobId}`);
  if (!response.ok) throw new Error("Failed to fetch job");
  return (await response.json()) as JobRecord;
}

export function loadPresets(): Preset[] {
  const stored = localStorage.getItem(PRESETS_KEY);
  if (stored) {
    try {
      return JSON.parse(stored) as Preset[];
    } catch (error) {
      return [];
    }
  }
  return [];
}

export function savePresets(presets: Preset[]) {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(presets));
}

export function loadActivePresetId() {
  return localStorage.getItem(ACTIVE_PRESET_KEY) || undefined;
}

export function saveActivePresetId(presetId?: string) {
  if (!presetId) {
    localStorage.removeItem(ACTIVE_PRESET_KEY);
  } else {
    localStorage.setItem(ACTIVE_PRESET_KEY, presetId);
  }
}
