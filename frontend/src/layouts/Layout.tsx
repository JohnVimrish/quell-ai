import { Outlet } from "react-router-dom";
import NavBar from "../components/NavBar";
import FloatingOrbs from "../components/FloatingOrbs";
import { AuthProvider } from "../components/AuthProvider";

export default function Layout() {
  return (
    <AuthProvider>
      <div className="app-shell">
        <FloatingOrbs />
        <NavBar />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </AuthProvider>
  );
}

