import React from "react";
import { formatStatValue } from "../../utils/format";
import { formatTimestamp } from "../../utils/time";

type StatCardProps = {
  label: string;
  value: number | null;
  unit: string;
  ts?: string;
  quality?: "good" | "stale" | "bad";
};

export function StatCard({ label, value, unit, ts, quality }: StatCardProps) {
  const qualityClass = quality ? `stat-quality quality-${quality}` : "stat-quality quality-good";
  
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {formatStatValue(value, unit)}
      </div>
      {ts && <div className="stat-text" style={{ fontSize: 11, marginTop: 4, opacity: 0.8 }}>{formatTimestamp(ts)}</div>}
      <div className={qualityClass}>{quality || "good"}</div>
    </div>
  );
}
