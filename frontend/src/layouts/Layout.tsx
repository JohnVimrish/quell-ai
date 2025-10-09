import { Outlet } from "react-router-dom";
import NavBar from "../components/NavBar";
import FloatingOrbs from "../components/FloatingOrbs";

export default function Layout() {
  return (
    <div className="app-shell">
      <FloatingOrbs />
      <NavBar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}

