import { type ReactNode, type CSSProperties } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  hover3D?: boolean;
}

export default function GlassCard({ children, className = "", style, hover3D = true }: GlassCardProps) {
  const baseClass = "glass-card";
  const hoverClass = hover3D ? "glass-card-3d" : "";
  
  return (
    <>
      <style>
        {`
          .glass-card {
            background: var(--glass-bg-strong);
            backdrop-filter: blur(var(--blur-strong));
            border: 2px solid var(--glass-border);
            border-radius: var(--radius-xl);
            box-shadow: var(--glass-shadow-strong);
            padding: 40px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          }

          .glass-card-3d {
            position: relative;
            transform-style: preserve-3d;
          }

          .glass-card-3d:hover {
            transform: translateY(-8px) rotateX(2deg) rotateY(-2deg);
            box-shadow: var(--shadow-3d);
            border-color: var(--color-orange-300);
          }

          .glass-card-3d::before {
            content: "";
            position: absolute;
            inset: -2px;
            background: var(--gradient-orange-green);
            border-radius: var(--radius-xl);
            opacity: 0;
            transition: opacity 0.4s ease;
            z-index: -1;
          }

          .glass-card-3d:hover::before {
            opacity: 0.1;
          }
        `}
      </style>
      <div 
        className={`${baseClass} ${hoverClass} ${className}`}
        style={style}
      >
        {children}
      </div>
    </>
  );
}

