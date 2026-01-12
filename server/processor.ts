import { appendLog, getJob, updateJob, writeArtifact } from "./storage";

type TranscriptSegment = {
  start: number;
  end: number;
  text: string;
};

const STEP_DELAY_MS = 650;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function formatTimestamp(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  const pad = (value: number, size = 2) => String(value).padStart(size, "0");
  return `${pad(hours)}:${pad(minutes)}:${pad(secs)},${pad(ms, 3)}`;
}

function segmentsToSrt(segments: TranscriptSegment[]) {
  return segments
    .map((segment, index) => {
      return `${index + 1}\n${formatTimestamp(segment.start)} --> ${formatTimestamp(
        segment.end
      )}\n${segment.text}\n`;
    })
    .join("\n");
}

function buildTranscriptFromText(text: string) {
  const words = text.split(/\s+/).filter(Boolean);
  const segments: TranscriptSegment[] = [];
  let cursor = 0;
  for (let i = 0; i < words.length; i += 8) {
    const chunk = words.slice(i, i + 8).join(" ");
    const start = cursor;
    const duration = 2.4 + (chunk.length % 3) * 0.4;
    const end = start + duration;
    segments.push({ start, end, text: chunk });
    cursor = end + 0.5;
  }
  return segments;
}

function buildHighlights(segments: TranscriptSegment[]) {
  return segments.slice(0, 3).map((segment, index) => ({
    id: `highlight-${index + 1}`,
    start: segment.start,
    end: segment.end,
    summary: segment.text.slice(0, 80),
  }));
}

export async function processJob(jobId: string) {
  const job = await getJob(jobId);
  if (!job) return;

  await updateJob(jobId, { status: "processing", progress: 5 });
  await appendLog(jobId, "Step 1/5: validate input");
  await sleep(STEP_DELAY_MS);

  const jobLatest = await getJob(jobId);
  if (!jobLatest) return;

  if (jobLatest.sourceType === "youtube" && !jobLatest.input.transcript) {
    await appendLog(jobId, "Captions not available. Upload a file instead. This demo does not download YouTube video/audio.");
    await updateJob(jobId, {
      status: "error",
      progress: 100,
      errorMessage:
        "Captions not available. Upload a file instead. This demo does not download YouTube video/audio.",
    });
    return;
  }

  await updateJob(jobId, { progress: 20 });
  await appendLog(jobId, "Step 2/5: extract/transcribe");
  await sleep(STEP_DELAY_MS);

  let transcriptText = "";
  if (jobLatest.sourceType === "upload") {
    const input = jobLatest.input;
    transcriptText = `Demo transcript for ${input.originalName}. This placeholder transcript simulates spoken content, highlighting key points about infinity creator workflows, branding, and export artifacts.`;
  } else {
    transcriptText = jobLatest.input.transcript || "";
  }

  const segments = buildTranscriptFromText(transcriptText);
  await updateJob(jobId, { progress: 45 });
  await appendLog(jobId, "Step 3/5: segment/highlight");
  await sleep(STEP_DELAY_MS);

  const highlights = buildHighlights(segments);
  await updateJob(jobId, { progress: 70 });
  await appendLog(jobId, "Step 4/5: export artifacts");
  await sleep(STEP_DELAY_MS);

  const manifest = {
    id: jobLatest.id,
    createdAt: jobLatest.createdAt,
    sourceType: jobLatest.sourceType,
    language: jobLatest.language,
    presetId: jobLatest.presetId,
    source: jobLatest.input,
    transcriptLength: transcriptText.length,
    highlights,
    artifacts: ["manifest.json", "subtitles.srt", "credits.txt"],
    generatedAt: new Date().toISOString(),
  };

  const creditsLines = [
    "Infinity Creator Tool - Provenance Report",
    `Job ID: ${jobLatest.id}`,
    `Source type: ${jobLatest.sourceType}`,
  ];

  if (jobLatest.sourceType === "youtube") {
    creditsLines.push(`YouTube URL: ${(jobLatest.input as any).url}`);
    creditsLines.push(`Title: ${(jobLatest.input as any).oembed?.title ?? "Unknown"}`);
    creditsLines.push(`Channel: ${(jobLatest.input as any).oembed?.author_name ?? "Unknown"}`);
    creditsLines.push(`Thumbnail: ${(jobLatest.input as any).oembed?.thumbnail_url ?? "Unknown"}`);
  } else {
    creditsLines.push(`Original filename: ${(jobLatest.input as any).originalName}`);
  }

  creditsLines.push(
    "Disclaimer: This demo does not download YouTube video/audio and is provided for educational purposes. Ensure you have rights to process uploaded media and comply with platform terms of service."
  );

  await writeArtifact(jobId, "manifest.json", JSON.stringify(manifest, null, 2));
  await writeArtifact(jobId, "subtitles.srt", segmentsToSrt(segments));
  await writeArtifact(jobId, "credits.txt", creditsLines.join("\n"));

  await updateJob(jobId, { status: "complete", progress: 100 });
  await appendLog(jobId, "Step 5/5: complete");
}
