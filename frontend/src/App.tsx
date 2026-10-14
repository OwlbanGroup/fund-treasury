import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { getHealth, type Health } from "./api";
import Dashboard from "./pages/Dashboard";
import Entities from "./pages/Entities";
import Accounts from "./pages/Accounts";
import Payments from "./pages/Payments";
import Forecast from "./pages/Forecast";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/entities", label: "Entities", end: false },
  { to: "/accounts", label: "Accounts", end: false },
  { to: "/payments", label: "Payments", end: false },
  { to: "/forecast", label: "Forecast", end: false },
];

function HealthBadge() {
  const [health, setHealth] = useState<Health | null>(null);
  const [down, setDown] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getHealth()
        .then((h) => {
          if (!alive) return;
          setHealth(h);
          setDown(false);
        })
        .catch(() => alive && setDown(true));
    load();
    const t = setInterval(load, 15_000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (down) return <span className="badge badge-error">API offline</span>;
  if (!health) return <span className="badge">…</span>;
  return (
    <span className="badge badge-ok" title={`database: ${health.database}`}>
      {health.status} · kyriba:{health.kyriba_mode} · bank:{health.bank_mode}
    </span>
  );
}

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <div>
            <div className="brand-name">Fund Treasury</div>
            <div className="brand-sub">Treasury management</div>
          </div>
        </div>
        <nav>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <HealthBadge />
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/forecast" element={<Forecast />} />
        </Routes>
      </main>
    </div>
  );
}
