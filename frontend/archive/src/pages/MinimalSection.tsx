import type { ReactNode } from "react";
import { useAuth } from "../components/AuthProvider";

interface MinimalSectionProps {
  title: string;
  description: string;
  actionLabel?: string;
  aside?: ReactNode;
}

export default function MinimalSection({ title, description, actionLabel = "Engage with the Application", aside }: MinimalSectionProps) {
  const { engage } = useAuth();
  return (
    <section className="minimal-section section-padding">
      <div className="glass-panel">
        <div style={{ display: "grid", gap: "32px" }}>
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          <button className="button-primary" style={{ justifySelf: "flex-start", width: "fit-content" }} onClick={engage}>
            {actionLabel}
          </button>
        </div>
        {aside}
      </div>
    </section>
  );
}



