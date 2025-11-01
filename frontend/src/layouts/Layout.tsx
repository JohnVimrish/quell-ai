import { Outlet } from "react-router-dom";
import NavBar from "../components/NavBar";
import FloatingOrbs from "../components/FloatingOrbs";
import MessageLabButton from "../components/MessageLabButton";

export default function Layout() {
  return (
    <div className="app-shell">
      <FloatingOrbs />
      <NavBar />
      <MessageLabButton />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
