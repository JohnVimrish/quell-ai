import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource-variable/inter";
import "./styles/theme.css";
import App from "./App";
import Authenticator from "./auth/Authenticator";

function mountReactApp(rootEl: HTMLElement) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

function integrateBaseHtml() {
  // Progressive enhancement: attach login to open authenticator modal
  function isLoginNode(el: Element) {
    const txt = (el.textContent || "").trim().toLowerCase();
    if (!txt) return false;
    return txt === "log in" || txt === "login";
  }

  const candidates = Array.from(document.querySelectorAll("#loginBtn, button, a"));
  const loginTargets = candidates.filter(isLoginNode);

  function openAuthModal(pushUrl: boolean = false) {
    let container = document.getElementById("auth-modal-root");
    if (!container) {
      container = document.createElement("div");
      container.id = "auth-modal-root";
      container.style.position = "fixed";
      container.style.inset = "0";
      container.style.zIndex = "9999";
      document.body.appendChild(container);
    }

    if (pushUrl) {
      // Push /login into history to reflect state
      const target = "/login";
      if (location.pathname !== target) {
        history.pushState({ modal: "login" }, "", target);
      }
    }

    const onClose = () => {
      if (!container) return;
      ReactDOM.createRoot(container).unmount();
      container.remove();
      // If URL indicates modal state, navigate back to restore previous route
      try {
        if (location.pathname === "/login") {
          history.back();
        }
      } catch {}
    };

    ReactDOM.createRoot(container).render(
      <React.StrictMode>
        <Authenticator onClose={onClose} />
      </React.StrictMode>
    );
  }

  loginTargets.forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openAuthModal(true);
    });
  });

  // Open modal automatically when navigating directly to /login
  if (location.pathname === "/login") {
    openAuthModal(false);
  }

  // Close modal on browser back/forward if container is present and leaving /login
  window.addEventListener("popstate", () => {
    const modalRoot = document.getElementById("auth-modal-root");
    if (modalRoot && location.pathname !== "/login") {
      try {
        ReactDOM.createRoot(modalRoot).unmount();
        modalRoot.remove();
      } catch {}
    }
    if (!modalRoot && location.pathname === "/login") {
      openAuthModal(false);
    }
  });
}

const rootEl = document.getElementById("root");
if (rootEl) {
  mountReactApp(rootEl);
} else {
  // No root present; treat backend/templates/base.html as the DOM and enhance it.
  integrateBaseHtml();
}

