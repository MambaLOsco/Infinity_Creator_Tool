import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createUploadJob,
  createYoutubeJob,
  loadActivePresetId,
  loadPresets,
} from "../lib/store";
import { Preset } from "../lib/types";
import { buildEmbedUrl, extractVideoId, fetchYoutubeOembed, isValidYoutubeUrl } from "../lib/youtube";

const NewJob = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"upload" | "youtube">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [presets, setPresets] = useState<Preset[]>([]);
  const [presetId, setPresetId] = useState<string | undefined>();
  const [metadata, setMetadata] = useState<{ title?: string; author_name?: string; thumbnail_url?: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedPresets = loadPresets();
    setPresets(storedPresets);
    setPresetId(loadActivePresetId() ?? storedPresets[0]?.id);
  }, []);

  const isYoutubeValid = useMemo(() => isValidYoutubeUrl(url), [url]);
  const videoId = useMemo(() => extractVideoId(url) ?? "", [url]);

  useEffect(() => {
    if (mode !== "youtube" || !isYoutubeValid) {
      setMetadata(null);
      return;
    }
    fetchYoutubeOembed(url).then(setMetadata).catch(() => setMetadata(null));
  }, [mode, url, isYoutubeValid]);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "upload") {
        if (!file) {
          setError("Please select a file to upload.");
          return;
        }
        const { jobId } = await createUploadJob(file, language, presetId);
        navigate(`/jobs/${jobId}`);
      } else {
        if (!isYoutubeValid) {
          setError("Please paste a valid YouTube URL.");
          return;
        }
        const { jobId } = await createYoutubeJob(url, language, presetId);
        navigate(`/jobs/${jobId}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>New Job</h1>
          <p>Create a new Infinity Creator job from an upload or YouTube link.</p>
        </div>
      </header>
      <div className="card">
        <div className="toggle-row">
          <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}>Upload</button>
          <button className={mode === "youtube" ? "active" : ""} onClick={() => setMode("youtube")}>YouTube</button>
        </div>
        {mode === "upload" ? (
          <div className="form-grid">
            <label>
              Upload media
              <input
                type="file"
                accept="audio/*,video/*"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
          </div>
        ) : (
          <div className="form-grid">
            <label>
              YouTube URL
              <input
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
              />
            </label>
            {isYoutubeValid && videoId && (
              <div className="youtube-preview">
                <iframe title="YouTube preview" src={buildEmbedUrl(videoId)} allowFullScreen />
                <div>
                  <h3>{metadata?.title ?? "Loading metadata..."}</h3>
                  <p>{metadata?.author_name ?? ""}</p>
                  <p className="hint">
                    This demo only pulls captions. If captions are unavailable, we will ask you to upload a file instead.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="form-grid">
          <label>
            Language
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </label>
          <label>
            Preset
            <select value={presetId} onChange={(event) => setPresetId(event.target.value)}>
              {presets.length === 0 && <option value="">No presets yet</option>}
              {presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <button
          className="primary"
          onClick={handleSubmit}
          disabled={submitting || (mode === "youtube" && !isYoutubeValid)}
        >
          {submitting ? "Creating..." : "Run Job"}
        </button>
      </div>
    </section>
  );
};

export default NewJob;
