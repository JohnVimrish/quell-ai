import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const PlaceholderPage = lazy(() => import("./pages/PlaceholderPage"));

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
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="features" element={<PlaceholderPage title="Features" />} />
            <Route path="pricing" element={<PlaceholderPage title="Pricing" />} />
            <Route path="faq" element={<PlaceholderPage title="FAQs" />} />
            <Route path="contact" element={<PlaceholderPage title="Contact" />} />
            <Route path="login" element={<PlaceholderPage title="Login" />} />
            <Route path="register" element={<PlaceholderPage title="Sign Up" />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
