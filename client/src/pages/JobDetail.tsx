import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchJob } from "../lib/store";
import { JobRecord } from "../lib/types";

const JobDetail = () => {
  const { jobId } = useParams();
  const [job, setJob] = useState<JobRecord | null>(null);
  const [manifest, setManifest] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    let timer: number | undefined;

    const load = async () => {
      const data = await fetchJob(jobId);
      setJob(data);
      setLoading(false);
      if (data.status === "queued" || data.status === "processing") {
        timer = window.setTimeout(load, 1500);
      }
    };

    load();
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  useEffect(() => {
    if (!jobId || job?.status !== "complete") return;
    fetch(`/api/jobs/${jobId}/artifacts/manifest.json`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setManifest)
      .catch(() => setManifest(null));
  }, [jobId, job?.status]);

  const artifacts = useMemo(() => {
    if (!job) return [];
    return Object.keys(job.artifacts || {});
  }, [job]);

  if (loading) {
    return <div className="card">Loading job...</div>;
  }

  if (!job) {
    return <div className="card">Job not found.</div>;
  }

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>Job Detail</h1>
          <p>{job.input?.originalName || job.input?.oembed?.title || job.input?.url}</p>
        </div>
        <Link className="secondary" to="/">
          Back to Dashboard
        </Link>
      </header>

      <div className="card">
        <div className="progress">
          <div className="progress-bar" style={{ width: `${job.progress}%` }} />
        </div>
        <div className="progress-meta">
          <span>Status: {job.status}</span>
          <span>{job.progress}%</span>
        </div>
        {job.status === "error" && (
          <div className="error-banner">
            {job.errorMessage || "Something went wrong."}
          </div>
        )}
        {job.status === "error" && job.sourceType === "youtube" && (
          <div className="hint">
            Captions are required for YouTube jobs. Upload a file instead to continue.
          </div>
        )}
      </div>

      <div className="grid two">
        <div className="card">
          <h3>Logs</h3>
          <pre className="log-view">
            {(job.logs || []).slice(0, 20).join("\n") || "No logs yet."}
          </pre>
        </div>
        <div className="card">
          <h3>Artifacts</h3>
          {job.status === "complete" ? (
            <div className="artifact-list">
              {artifacts.map((name) => (
                <a key={name} href={`/api/jobs/${job.id}/artifacts/${name}`} className="download">
                  Download {name}
                </a>
              ))}
            </div>
          ) : (
            <p>Artifacts will appear when processing completes.</p>
          )}
        </div>
      </div>

      {manifest && (
        <div className="card">
          <h3>Transcript Highlights</h3>
          <p>Transcript length: {manifest.transcriptLength} characters</p>
          <ul>
            {manifest.highlights?.map((highlight: any) => (
              <li key={highlight.id}>
                {highlight.summary} ({highlight.start}s - {highlight.end}s)
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

export default JobDetail;
