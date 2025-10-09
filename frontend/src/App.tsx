import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";
import MinimalSection from "./pages/MinimalSection";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const CallsPage = lazy(() => import("./pages/CallsPage"));
const ContactsPage = lazy(() => import("./pages/ContactsPage"));
const TextsPage = lazy(() => import("./pages/TextsPage"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));

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
  { path: "faq", title: "FAQs", description: "Answers to common questions about AI call handling, compliance, and integrations." },
];

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="calls" element={<CallsPage />} />
            <Route path="contacts" element={<ContactsPage />} />
            <Route path="texts" element={<TextsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<SignupPage />} />
            {simplePages.map(({ path, title, description }) => (
              <Route key={path} path={path} element={<MinimalSection title={title} description={description} />} />
            ))}
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
