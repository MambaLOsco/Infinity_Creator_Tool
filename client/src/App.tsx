import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import NewJob from "./pages/NewJob";
import JobDetail from "./pages/JobDetail";
import Settings from "./pages/Settings";

const App = () => {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">Infinity Creator</div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/new">New Job</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
        <div className="disclaimer">
          Never upload secrets. This demo stores jobs locally.
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewJob />} />
          <Route path="/jobs/:jobId" element={<JobDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
