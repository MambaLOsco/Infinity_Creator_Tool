import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import express from "express";
import multer from "multer";
import {
  appendLog,
  artifactExists,
  createJob,
  getJob,
  getJobInputPath,
  listJobs,
  readArtifactStream,
  updateJob,
} from "./storage";
import { processJob } from "./processor";

const MAX_FILE_SIZE = 25 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([".mp3", ".mp4", ".wav", ".mov", ".m4a", ".webm"]);

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_FILE_SIZE },
});

export const router = express.Router();

router.get("/api/jobs", async (_req, res) => {
  const jobs = await listJobs();
  res.json(jobs);
});

router.get("/api/jobs/:id", async (req, res) => {
  const job = await getJob(req.params.id);
  if (!job) {
    res.status(404).json({ error: "Job not found" });
    return;
  }
  res.json(job);
});

router.get("/api/jobs/:id/artifacts/:name", async (req, res) => {
  const { id, name } = req.params;
  const exists = await artifactExists(id, name);
  if (!exists) {
    res.status(404).json({ error: "Artifact not found" });
    return;
  }
  const stream = await readArtifactStream(id, name);
  if (!stream) {
    res.status(404).json({ error: "Artifact not found" });
    return;
  }
  res.setHeader("Content-Disposition", `attachment; filename=\"${name}\"`);
  stream.pipe(res);
});

router.post("/api/jobs/upload", upload.single("file"), async (req, res) => {
  const file = req.file;
  const language = String(req.body.language ?? "en");
  const presetId = req.body.presetId ? String(req.body.presetId) : undefined;

  if (!file) {
    res.status(400).json({ error: "File is required" });
    return;
  }

  const ext = path.extname(file.originalname).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    res.status(400).json({
      error: "Unsupported file type. Please upload audio/video files (mp3, mp4, wav, mov, m4a, webm).",
    });
    return;
  }

  const jobId = crypto.randomUUID();
  const job = await createJob({
    id: jobId,
    status: "queued",
    progress: 0,
    sourceType: "upload",
    language,
    presetId,
    input: {
      filename: file.originalname,
      originalName: file.originalname,
      size: file.size,
      mimeType: file.mimetype,
    },
  });

  const destination = getJobInputPath(jobId, file.originalname);
  await fs.promises.writeFile(destination, file.buffer);
  await appendLog(jobId, `Uploaded file ${file.originalname}`);

  processJob(jobId);

  res.json({ jobId: job.id });
});

router.post("/api/jobs/youtube", async (req, res) => {
  const { url, language = "en", presetId } = req.body ?? {};
  if (!url || typeof url !== "string") {
    res.status(400).json({ error: "YouTube URL is required" });
    return;
  }

  const videoId = extractVideoId(url);
  if (!videoId) {
    res.status(400).json({ error: "Invalid YouTube URL" });
    return;
  }

  const jobId = crypto.randomUUID();
  const job = await createJob({
    id: jobId,
    status: "queued",
    progress: 0,
    sourceType: "youtube",
    language: String(language),
    presetId: presetId ? String(presetId) : undefined,
    input: {
      url,
      videoId,
    },
  });

  try {
    const oembed = await fetchOembed(url);
    if (oembed) {
      await updateJob(jobId, {
        input: {
          url,
          videoId,
          oembed,
        },
      });
    }

    const transcript = await fetchTranscript(videoId, String(language));
    if (transcript) {
      await updateJob(jobId, {
        input: {
          url,
          videoId,
          oembed,
          transcript,
        },
      });
    }
  } catch (error) {
    await appendLog(jobId, "Failed to fetch YouTube metadata/transcript.");
  }

  processJob(jobId);

  res.json({ jobId: job.id });
});

function extractVideoId(url: string) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtu.be")) {
      return parsed.pathname.replace("/", "");
    }
    if (parsed.hostname.includes("youtube.com")) {
      const v = parsed.searchParams.get("v");
      if (v) return v;
      const match = parsed.pathname.match(/\/embed\/(.+)/);
      if (match) return match[1];
    }
  } catch (error) {
    return null;
  }
  return null;
}

async function fetchOembed(url: string) {
  const response = await fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`);
  if (!response.ok) return null;
  return (await response.json()) as {
    title?: string;
    author_name?: string;
    author_url?: string;
    thumbnail_url?: string;
    provider_name?: string;
  };
}

function decodeXml(text: string) {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/<\/?[^>]+>/g, "");
}

async function fetchTranscript(videoId: string, language: string) {
  const languages = [language, "en"];
  for (const lang of languages) {
    const response = await fetch(
      `https://video.google.com/timedtext?lang=${encodeURIComponent(lang)}&v=${encodeURIComponent(videoId)}`
    );
    if (!response.ok) continue;
    const raw = await response.text();
    if (!raw.includes("<text")) continue;
    const matches = [...raw.matchAll(/<text[^>]*>([\s\S]*?)<\/text>/g)];
    const lines = matches.map((match) => decodeXml(match[1] ?? "")).filter(Boolean);
    const transcript = lines.join(" ");
    if (transcript) return transcript;
  }
  return null;
}
