import React from "react";

type CardProps = {
  title?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
};

export function Card({ title, actions, children }: CardProps) {
  return (
    <section className="card">
      {title || actions ? (
        <div className="card-header">
          {title ? <h3 className="card-title">{title}</h3> : <div />}
          {actions ? <div className="card-actions">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
