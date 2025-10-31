import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";

const LandingPage = lazy(() => import("./pages/LandingPage"));
// Use the unified authenticator for consistency with base.html
import Authenticator from "./auth/Authenticator";
const DocumentsPage = lazy(() => import("./pages/DocumentsPage"));
const LabsPlayground = lazy(() => import("./pages/LabsPlayground"));

function LoadingFallback() {
  return (
    <div className="app-loading">
      <div className="loading-spinner" />
      <span>Loading experience…</span>
    </div>
  );
}

// Archived routes removed: dashboard, meetings, texts, settings, why, message-understanding, register, simple pages

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="labs/dev-playground" element={<LabsPlayground />} />
            <Route path="login" element={<Authenticator />} />
            { /* Removed register and simple pages */ }
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
