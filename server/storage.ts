import { createReadStream, existsSync } from "node:fs";
import { mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export type JobStatus = "queued" | "processing" | "complete" | "error";
export type SourceType = "upload" | "youtube";

export interface JobInputUpload {
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
}

export interface JobInputYoutube {
  url: string;
  videoId: string;
  oembed?: {
    title?: string;
    author_name?: string;
    author_url?: string;
    thumbnail_url?: string;
    provider_name?: string;
  };
  transcript?: string;
}

export interface JobRecord {
  id: string;
  status: JobStatus;
  progress: number;
  createdAt: string;
  updatedAt: string;
  sourceType: SourceType;
  language: string;
  presetId?: string;
  input: JobInputUpload | JobInputYoutube;
  logs: string[];
  artifacts: Record<string, string>;
  errorMessage?: string;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.resolve(__dirname, "..", "data", "jobs");

async function ensureDir(dir: string) {
  await mkdir(dir, { recursive: true });
}

function jobDir(jobId: string) {
  return path.join(DATA_DIR, jobId);
}

function jobFile(jobId: string) {
  return path.join(jobDir(jobId), "job.json");
}

export async function createJob(partial: Omit<JobRecord, "createdAt" | "updatedAt" | "logs" | "artifacts">) {
  const now = new Date().toISOString();
  const record: JobRecord = {
    ...partial,
    createdAt: now,
    updatedAt: now,
    logs: [],
    artifacts: {},
  };
  await ensureDir(jobDir(record.id));
  await ensureDir(path.join(jobDir(record.id), "input"));
  await ensureDir(path.join(jobDir(record.id), "artifacts"));
  await writeFile(jobFile(record.id), JSON.stringify(record, null, 2), "utf-8");
  return record;
}

export async function listJobs(): Promise<JobRecord[]> {
  await ensureDir(DATA_DIR);
  const entries = await readdir(DATA_DIR);
  const jobs: JobRecord[] = [];
  for (const entry of entries) {
    const filePath = path.join(DATA_DIR, entry, "job.json");
    if (!existsSync(filePath)) continue;
    try {
      const raw = await readFile(filePath, "utf-8");
      const parsed = JSON.parse(raw) as JobRecord;
      jobs.push(parsed);
    } catch (error) {
      console.error("Failed to read job", entry, error);
    }
  }
  return jobs.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function getJob(jobId: string): Promise<JobRecord | null> {
  try {
    const raw = await readFile(jobFile(jobId), "utf-8");
    return JSON.parse(raw) as JobRecord;
  } catch (error) {
    return null;
  }
}

export async function updateJob(jobId: string, update: Partial<JobRecord>) {
  const record = await getJob(jobId);
  if (!record) return null;
  const next = {
    ...record,
    ...update,
    updatedAt: new Date().toISOString(),
  } satisfies JobRecord;
  await writeFile(jobFile(jobId), JSON.stringify(next, null, 2), "utf-8");
  return next;
}

export async function appendLog(jobId: string, message: string) {
  const record = await getJob(jobId);
  if (!record) return null;
  const next = {
    ...record,
    logs: [`${new Date().toISOString()} ${message}`, ...record.logs],
    updatedAt: new Date().toISOString(),
  } satisfies JobRecord;
  await writeFile(jobFile(jobId), JSON.stringify(next, null, 2), "utf-8");
  return next;
}

export async function writeArtifact(jobId: string, name: string, contents: string) {
  const record = await getJob(jobId);
  if (!record) return null;
  const filePath = path.join(jobDir(jobId), "artifacts", name);
  await writeFile(filePath, contents, "utf-8");
  const next = {
    ...record,
    artifacts: {
      ...record.artifacts,
      [name]: filePath,
    },
    updatedAt: new Date().toISOString(),
  } satisfies JobRecord;
  await writeFile(jobFile(jobId), JSON.stringify(next, null, 2), "utf-8");
  return next;
}

export async function artifactExists(jobId: string, name: string) {
  const record = await getJob(jobId);
  if (!record) return false;
  const filePath = record.artifacts[name];
  if (!filePath) return false;
  try {
    const fileStat = await stat(filePath);
    return fileStat.isFile();
  } catch (error) {
    return false;
  }
}

export async function readArtifactStream(jobId: string, name: string) {
  const record = await getJob(jobId);
  if (!record) return null;
  const filePath = record.artifacts[name];
  if (!filePath) return null;
  return createReadStream(filePath);
}

export function getJobInputPath(jobId: string, filename: string) {
  return path.join(jobDir(jobId), "input", filename);
}

export function getArtifactsDir(jobId: string) {
  return path.join(jobDir(jobId), "artifacts");
}
