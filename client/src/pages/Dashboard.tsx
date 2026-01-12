import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJobs } from "../lib/store";
import { JobRecord } from "../lib/types";

const statusLabels: Record<string, string> = {
  queued: "Queued",
  processing: "Processing",
  complete: "Complete",
  error: "Error",
};

const Dashboard = () => {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs()
      .then(setJobs)
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Track your recent Infinity Creator jobs and downloads.</p>
        </div>
        <Link className="primary" to="/new">
          New Job
        </Link>
      </header>
      {loading ? (
        <div className="card">Loading jobs...</div>
      ) : jobs.length === 0 ? (
        <div className="card">No jobs yet. Start one from the New Job page.</div>
      ) : (
        <div className="job-list">
          {jobs.map((job) => (
            <Link key={job.id} className="card job-item" to={`/jobs/${job.id}`}>
              <div>
                <h3>{job.input?.originalName || job.input?.oembed?.title || job.input?.url}</h3>
                <p>
                  {job.sourceType.toUpperCase()} · {new Date(job.createdAt).toLocaleString()}
                </p>
              </div>
              <span className={`status ${job.status}`}>{statusLabels[job.status]}</span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
};

export default Dashboard;
