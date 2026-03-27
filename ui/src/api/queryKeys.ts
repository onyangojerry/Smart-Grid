export const queryKeys = {
  sites: () => ["sites"] as const,
  site: (id: string) => ["sites", id] as const,
  devices: (siteId: string) => ["devices", siteId] as const,
  assets: (siteId: string) => ["assets", siteId] as const,
  telemetryLatest: (siteId: string) => ["telemetry", siteId, "latest"] as const,
  telemetryHistory: (siteId: string, key: string) => ["telemetry", siteId, "history", key] as const,
  optimizationRuns: (siteId: string) => ["optimization", siteId] as const,
  optimizationRunDetail: (runId: string) => ["optimization", "run", runId] as const,
  commands: (siteId: string) => ["commands", siteId] as const,
  savings: (siteId: string) => ["savings", siteId] as const,
  simulation: (siteId: string, simId: string) => ["simulation", siteId, simId] as const,
  alerts: (siteId: string) => ["alerts", siteId] as const,
  alertCounts: (siteId: string) => ["alerts", siteId, "count"] as const,
  alert: (alertId: string) => ["alerts", "detail", alertId] as const
} as const;
