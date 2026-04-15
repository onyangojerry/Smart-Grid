import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import "../../styles/features.css";

export function EdgeLogsPage() {
  const { siteId } = useParams();
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    
    const fetchLogs = async () => {
      try {
        // Assuming the backend provides logs at /api/v1/edge/logs
        // The log file path is configurable via EDGE_LOG_FILE_PATH env var on the backend.
        // For the frontend, we'll assume a default or derive it if possible.
        // For now, we'll use a generic path and let the backend handle the default.
        const url = `/api/v1/edge/logs`; 
        
        eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
          // Append new log lines to the state
          setLogs((prevLogs) => [...prevLogs, event.data]);
        };

        eventSource.onerror = (err) => {
          setError(new Error(`EventSource failed: ${err}`));
          eventSource?.close();
        };
      } catch (err: any) {
        setError(err);
      }
    };

    fetchLogs();

    return () => {
      // Clean up the EventSource connection when the component unmounts
      eventSource?.close();
    };
  }, [siteId]); // Re-run if siteId changes

  return (
    <div className="page-content">
      <PageHeader title="Edge Logs" subtitle={siteId || "Global"} />

      <Card title="Live Edge Logs">
        {error ? (
          <ErrorBanner error={error} />
        ) : (
          <pre style={{ 
            whiteSpace: "pre-wrap", 
            wordBreak: "break-word", 
            maxHeight: "600px", 
            overflowY: "auto", 
            backgroundColor: "#1e1e1e", 
            color: "#d4d4d4", 
            padding: "10px",
            borderRadius: "4px"
          }}>
            {logs.join("\n")}
          </pre>
        )}
      </Card>
    </div>
  );
}
