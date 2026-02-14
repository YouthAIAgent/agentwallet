import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import Wallets from "./pages/Wallets";
import Transactions from "./pages/Transactions";
import Analytics from "./pages/Analytics";
import Policies from "./pages/Policies";
import AuditLog from "./pages/AuditLog";
import Billing from "./pages/Billing";
import PdaWallets from "./pages/PdaWallets";
import Login from "./pages/Login";
import { isAuthenticated } from "./api";

function ProtectedLayout() {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Sidebar />
      <main className="ml-60 min-h-screen">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/wallets" element={<Wallets />} />
            <Route path="/pda-wallets" element={<PdaWallets />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/audit-log" element={<AuditLog />} />
            <Route path="/billing" element={<Billing />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  );
}
