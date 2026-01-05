import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import otAdapter from "../../services/ot";
import type { OtPcapJob } from "../../types/ot";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import OtDrawer from "../../components/ot/OtDrawer";
import TableSkeleton from "../../components/ot/TableSkeleton";
import { formatRelativeTime } from "../../lib/otFormat";

const PcapPage = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<OtPcapJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<OtPcapJob | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await otAdapter.listPcapJobs();
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load PCAP jobs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs().catch((err) => console.error(err));
  }, [loadJobs]);

  useEffect(() => {
    if (!selectedJob) return;
    const updated = jobs.find((job) => job.id === selectedJob.id);
    if (updated) setSelectedJob(updated);
  }, [jobs, selectedJob]);

  useEffect(() => {
    if (!jobs.some((job) => job.status === "queued" || job.status === "running")) {
      return;
    }
    const interval = window.setInterval(() => {
      loadJobs().catch((err) => console.error(err));
    }, 1200);
    return () => window.clearInterval(interval);
  }, [jobs, loadJobs]);

  const isValidFile = useMemo(() => {
    if (!selectedFile) return false;
    return /\.pcapng?$/.test(selectedFile.name.toLowerCase());
  }, [selectedFile]);

  const handleUpload = async () => {
    if (!selectedFile || !isValidFile) return;
    setUploading(true);
    setUploadProgress(10);
    const progressTimer = window.setInterval(() => {
      setUploadProgress((prev) => (prev >= 90 ? prev : prev + 10));
    }, 200);

    try {
      await otAdapter.createPcapJob(selectedFile);
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create PCAP job.");
    } finally {
      window.clearInterval(progressTimer);
      setUploading(false);
      setUploadProgress(100);
      window.setTimeout(() => setUploadProgress(0), 800);
      setSelectedFile(null);
    }
  };

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">PCAP Analysis</div>
          <div className="page-subtitle">Upload PCAP/PCAPNG to discover assets, communications, and detections.</div>
        </div>
      </div>

      <div className="card ot-upload-card">
        <div className="ot-upload-icon" aria-hidden="true">☁️</div>
        <div className="ot-upload-title">Drag & drop your PCAP files here or click to browse</div>
        <div className="ot-upload-subtitle">Supported: .pcap, .pcapng · Max file size: 1GB</div>
        <input
          type="file"
          className="ot-upload-input"
          accept=".pcap,.pcapng"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
        {selectedFile && !isValidFile ? (
          <div className="field-error">Unsupported file type. Upload .pcap or .pcapng.</div>
        ) : null}
        <div className="ot-upload-progress">
          <div
            className="ot-upload-progress-bar"
            style={{ width: uploadProgress ? `${uploadProgress}%` : "0%" }}
          />
        </div>
        <button type="button" className="btn" disabled={!isValidFile || uploading} onClick={handleUpload}>
          {uploading ? "Analyzing…" : "Analyze PCAP"}
        </button>
      </div>

      {loading ? (
        <div className="card">
          <TableSkeleton rows={5} columns={6} />
        </div>
      ) : error ? (
        <ErrorState
          message="Failed to load PCAP jobs. Please try again."
          details={error}
          onRetry={loadJobs}
        />
      ) : jobs.length === 0 ? (
        <EmptyState
          title="No PCAP jobs yet"
          message="Upload a capture to start analysis."
          action={
            <button type="button" className="btn" onClick={() => navigate("/ot/pcap")}>Upload PCAP</button>
          }
        />
      ) : (
        <div className="card table-wrap">
          <div className="card-header">
            <div>
              <div className="card-title">Recent PCAP Jobs</div>
              <div className="card-subtitle">Latest offline analysis submissions.</div>
            </div>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Uploaded at</th>
                <th>Status</th>
                <th>Assets</th>
                <th>Detections</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className="table-row-clickable"
                  onClick={() => setSelectedJob(job)}
                >
                  <td>{job.filename}</td>
                  <td className="muted">{formatRelativeTime(job.uploadedAt)}</td>
                  <td>
                    <span className={`status-pill status-${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="muted">{job.stats.assetsDiscovered}</td>
                  <td className="muted">{job.stats.detections}</td>
                  <td>
                    <button type="button" className="table-row-actions" onClick={(event) => event.stopPropagation()}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <OtDrawer
        title={selectedJob ? `Job Details: ${selectedJob.filename}` : "Job Details"}
        subtitle={selectedJob ? `Status: ${selectedJob.status}` : undefined}
        open={Boolean(selectedJob)}
        onClose={() => setSelectedJob(null)}
        footer={
          selectedJob ? (
            <div className="stack-horizontal">
              <button
                type="button"
                className="btn"
                onClick={() => navigate(`/ot/detections?pcapJobId=${selectedJob.id}`)}
              >
                View Detections
              </button>
              <button type="button" className="btn btn-ghost">Download report</button>
            </div>
          ) : null
        }
      >
        {selectedJob ? (
          <div className="stack-vertical">
            <div className="grid-2">
              <div className="card">
                <div className="card-title">Flows</div>
                <div className="card-value">{selectedJob.stats.flows}</div>
              </div>
              <div className="card">
                <div className="card-title">Top protocols</div>
                <div className="card-value">
                  {Object.keys(selectedJob.stats.protocols).length
                    ? Object.keys(selectedJob.stats.protocols).slice(0, 2).join(" · ")
                    : "—"}
                </div>
              </div>
              <div className="card">
                <div className="card-title">Assets discovered</div>
                <div className="card-value">{selectedJob.stats.assetsDiscovered}</div>
              </div>
              <div className="card">
                <div className="card-title">Detections</div>
                <div className="card-value">{selectedJob.stats.detections}</div>
              </div>
            </div>
            {selectedJob.error ? (
              <div className="card">
                <div className="card-title">Error</div>
                <p className="muted">{selectedJob.error}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </OtDrawer>
      </div>
    </div>
  );
};

export default PcapPage;
