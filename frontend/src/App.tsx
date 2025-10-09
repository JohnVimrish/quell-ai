import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";
import MinimalSection from "./pages/MinimalSection";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));

function LoadingFallback() {
  return (
    <div className="app-loading">
      <div className="loading-spinner" />
      <span>Loading experience…</span>
    </div>
  );
}

const simplePages = [
  { path: "features", title: "Product", description: "All the building blocks you need to orchestrate calls, texts, and automations without leaving your workspace." },
  { path: "pricing", title: "Pricing", description: "Transparent tiers with built-in AI automations and usage-based add-ons for scaling teams." },
  { path: "faq", title: "FAQs", description: "Answers to common questions about AI call handling, compliance, and integrations." },
  { path: "contact", title: "Contact", description: "Reach out to the team for onboarding support, enterprise plans, or custom integrations." },
  { path: "login", title: "Log in", description: "Access your communicator console and resume where you left off." },
  { path: "register", title: "Create an account", description: "Launch your communicator copilot in minutes with secure authentication and database setup." },
];

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            {simplePages.map(({ path, title, description }) => (
              <Route key={path} path={path} element={<MinimalSection title={title} description={description} />} />
            ))}
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
