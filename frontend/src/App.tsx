import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./components/AuthProvider";
import Layout from "./layouts/Layout";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
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

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route index element={<LandingPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="signup" element={<SignupPage />} />
            <Route element={<Layout />}>
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="labs/dev-playground" element={<LabsPlayground />} />
            </Route>
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
