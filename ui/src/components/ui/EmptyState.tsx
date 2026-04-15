import React from "react";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state card" style={{ borderStyle: "dashed", textAlign: "center" }}>
      <div className="empty-state-icon">🌿</div>
      <h3 className="empty-state-title">{title}</h3>
      {description ? <p className="empty-state-description">{description}</p> : null}
      {action ? (
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={action.onClick}>
          {action.label}
        </button>
      ) : null}
    </div>
  );
}
