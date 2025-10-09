import type { ReactNode } from "react";

interface MinimalSectionProps {
  title: string;
  description: string;
  actionLabel?: string;
  aside?: ReactNode;
}

export default function MinimalSection({ title, description, actionLabel = "Start building", aside }: MinimalSectionProps) {
  return (
    <section className="minimal-section section-padding">
      <div className="glass-panel">
        <div style={{ display: "grid", gap: "32px" }}>
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          <button className="button-primary" style={{ justifySelf: "flex-start", width: "fit-content" }}>{actionLabel}</button>
        </div>
        {aside}
      </div>
    </section>
  );
}



