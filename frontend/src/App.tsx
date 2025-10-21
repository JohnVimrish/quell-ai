import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";
import MinimalSection from "./pages/MinimalSection";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
// Archived (Oct 2025): Calls & Contacts routes
// const CallsPage = lazy(() => import("./pages/CallsPage"));
// const ContactsPage = lazy(() => import("./pages/ContactsPage"));
const MeetingsPage = lazy(() => import("./pages/MeetingsPage"));
const TextsPage = lazy(() => import("./pages/TextsPage"));
const DocumentsPage = lazy(() => import("./pages/DocumentsPage"));
// Archived (Oct 2025): Reports route
// const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const WhyQuellAI = lazy(() => import("./pages/WhyQuellAI"));
const MessageUnderstandingDemo = lazy(() => import("./pages/MessageUnderstandingDemo"));
const LabsPlayground = lazy(() => import("./pages/LabsPlayground"));

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
            <Route path="meetings" element={<MeetingsPage />} />
            { /* Archived (Oct 2025): calls, contacts */ }
            { /* <Route path="calls" element={<CallsPage />} /> */ }
            { /* <Route path="contacts" element={<ContactsPage />} /> */ }
            <Route path="texts" element={<TextsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            { /* Archived (Oct 2025): reports */ }
            { /* <Route path="reports" element={<ReportsPage />} /> */ }
            <Route path="settings" element={<SettingsPage />} />
            <Route path="why" element={<WhyQuellAI />} />
            <Route path="labs/message-understanding" element={<MessageUnderstandingDemo />} />
            <Route path="labs/dev-playground" element={<LabsPlayground />} />
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
