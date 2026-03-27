import React from "react";
import type { CommandStatus, DeviceStatus, AlertSeverity, AlertState } from "../../types";

const commandStatusColors: Record<CommandStatus, string> = {
  queued: "#9e9e9e",
  sent: "#1976d2",
  acknowledged: "#f9a825",
  executed: "#2e7d32",
  failed: "#c62828",
  rejected: "#ef6c00"
};

const deviceStatusColors: Record<DeviceStatus, string> = {
  active: "#2e7d32",
  inactive: "#9e9e9e",
  fault: "#c62828"
};

const alertSeverityColors: Record<AlertSeverity, string> = {
  info: "#1976d2",
  warning: "#f9a825",
  critical: "#c62828"
};

const alertStateColors: Record<AlertState, string> = {
  open: "#c62828",
  acknowledged: "#f9a825",
  resolved: "#2e7d32"
};

type BadgeProps = {
  kind: "command" | "device" | "severity" | "state" | "plain";
  value: string;
};

export function Badge({ kind, value }: BadgeProps) {
  let color = "#607d8b";
  if (kind === "command") {
    color = commandStatusColors[value as CommandStatus] || color;
  }
  if (kind === "device") {
    color = deviceStatusColors[value as DeviceStatus] || color;
  }
  if (kind === "severity") {
    color = alertSeverityColors[value as AlertSeverity] || color;
  }
  if (kind === "state") {
    color = alertStateColors[value as AlertState] || color;
  }
  return (
    <span style={{ background: `${color}22`, color, borderRadius: 999, padding: "2px 8px", fontSize: 12, fontWeight: 600 }}>
      {value}
    </span>
  );
}
