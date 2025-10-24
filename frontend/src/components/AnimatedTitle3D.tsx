import { useNavigate, useLocation } from "react-router-dom";

const sections = [
  { id: "about", label: "About", path: "/" },
  { id: "dashboard", label: "Dashboard", path: "/dashboard" },
  // Archived (Oct 2025): Calls, Contacts
  // { id: "calls", label: "Calls", path: "/calls" },
  // { id: "contacts", label: "Contacts", path: "/contacts" },
  { id: "texts", label: "Texts", path: "/texts" },
  // Archived (Oct 2025): Reports
  // { id: "reports", label: "Reports", path: "/reports" },
  { id: "settings", label: "Settings", path: "/settings" },
];

export default function AnimatedTitle3D() {
  const navigate = useNavigate();
  const location = useLocation();

  const getCurrentIndex = () => {
    return sections.findIndex((section) => section.path === location.pathname) || 0;
  };

  const handleSectionClick = (path: string) => {
    navigate(path);
  };

  return (
    <>
      <style>
        {`
          .title-3d-container {
            perspective: 1200px;
            width: 100%;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 40px 0;
          }

          .title-3d-wrapper {
            transform-style: preserve-3d;
            position: relative;
            width: fit-content;
          }

          .title-3d-section {
            font-size: clamp(2.5rem, 5vw, 4.5rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            cursor: pointer;
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-block;
            margin: 0 20px;
            position: relative;
            color: var(--color-grey-800);
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
          }

          .title-3d-section.active {
            color: #0ea5e9;
            transform: translateZ(40px) scale(1.1);
            text-shadow: 4px 4px 12px rgba(14, 165, 233, 0.3);
          }

          .title-3d-section.inactive {
            opacity: 0.4;
            transform: translateZ(-20px) scale(0.85);
          }

          .title-3d-section:hover:not(.active) {
            opacity: 0.7;
            transform: translateZ(20px) scale(1);
            color: var(--color-green-500);
          }

          .title-3d-underline {
            position: absolute;
            bottom: -10px;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #0ea5e9, #22d3ee);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 2px;
          }

          .title-3d-section.active .title-3d-underline {
            transform: scaleX(1);
          }

          @media (max-width: 768px) {
            .title-3d-container {
              height: 150px;
            }

            .title-3d-section {
              margin: 0 10px;
              font-size: clamp(1.8rem, 6vw, 2.5rem);
            }
          }
        `}
      </style>
      <div className="title-3d-container">
        <div className="title-3d-wrapper">
          {sections.map((section, index) => {
            const isActive = getCurrentIndex() === index;
            const isInactive = !isActive && getCurrentIndex() !== index;

            return (
              <span
                key={section.id}
                className={`title-3d-section ${isActive ? "active" : ""} ${isInactive ? "inactive" : ""}`}
                onClick={() => handleSectionClick(section.path)}
              >
                {section.label}
                <div className="title-3d-underline" />
              </span>
            );
          })}
        </div>
      </div>
    </>
  );
}
