import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function MessageLabButton() {
  const navigate = useNavigate();
  const location = useLocation();
  const goToLab = useCallback(() => {
    if (!location.pathname.startsWith("/labs/message-understanding")) {
      navigate("/labs/message-understanding");
    }
  }, [location.pathname, navigate]);

  if (location.pathname.startsWith("/labs/message-understanding")) {
    return null;
  }

  return (
    <button
      type="button"
      className="message-lab-launcher"
      onClick={goToLab}
      onMouseEnter={goToLab}
      onFocus={goToLab}
      aria-label="Enter Message Lab"
    >
      Message Lab
    </button>
  );
}
