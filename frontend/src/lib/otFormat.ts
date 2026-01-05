import type { OtCriticality, OtDetectionStatus, OtDirection, OtSeverity, OtSensorStatus } from "../types/ot";

export const formatTimestamp = (iso: string) => new Date(iso).toLocaleString();

export const formatRelativeTime = (iso: string) => {
  const time = new Date(iso).getTime();
  const diff = Date.now() - time;
  const minutes = Math.floor(diff / 60000);
  if (Number.isNaN(minutes)) return "—";
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

export const severityClass = (severity: OtSeverity) => {
  if (severity === "med") return "severity-medium";
  return `severity-${severity}`;
};

export const criticalityClass = (criticality: OtCriticality) =>
  criticality === "med" ? "severity-medium" : `severity-${criticality}`;

export const statusLabel = (status: OtDetectionStatus) =>
  status.replace("_", " ");

export const detectionStatusClass = (status: OtDetectionStatus) => {
  if (status === "in_progress") return "status-in-progress";
  return status === "closed" ? "status-closed" : "status-open";
};

export const sensorStatusClass = (status: OtSensorStatus) => `status-${status}`;

export const directionLabel = (direction: OtDirection) => direction;
