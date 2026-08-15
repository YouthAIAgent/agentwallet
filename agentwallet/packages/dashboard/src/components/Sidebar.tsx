import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Bot,
  Wallet,
  ArrowLeftRight,
  BarChart3,
  ShieldCheck,
  ScrollText,
  CreditCard,
  KeyRound,
  LogOut,
  Sun,
  Moon,
  Zap,
} from "lucide-react";
import Brand from "./Brand";
import { auth } from "../api";

const navItems = [
  { to: "/app", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/agents", icon: Bot, label: "Agents" },
  { to: "/wallets", icon: Wallet, label: "Wallets" },
  { to: "/pda-wallets", icon: KeyRound, label: "PDA Wallets" },
  { to: "/transactions", icon: ArrowLeftRight, label: "Transactions" },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/policies", icon: ShieldCheck, label: "Policies" },
  { to: "/audit-log", icon: ScrollText, label: "Audit Log" },
  { to: "/billing", icon: CreditCard, label: "Billing" },
  { to: "/playground", icon: Zap, label: "Playground" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const [light, setLight] = useState(
    () => localStorage.getItem("aw-theme") === "light"
  );

  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
    localStorage.setItem("aw-theme", light ? "light" : "dark");
  }, [light]);

  const handleLogout = () => {
    auth.logout();
    navigate("/login");
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-ink-900 border-r border-ink-800 flex flex-col z-40">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-ink-800">
        <Brand />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/app"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-600/10 text-brand-400 border border-brand-500/20"
                  : "text-ink-400 hover:text-ink-200 hover:bg-ink-800/60 border border-transparent"
              }`
            }
          >
            <Icon className="w-[18px] h-[18px] flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-ink-800 space-y-1">
        <button
          onClick={() => setLight(!light)}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-ink-500 hover:text-ink-300 hover:bg-ink-800/60 transition-colors"
          title="Toggle light/dark theme"
        >
          {light ? (
            <Moon className="w-[18px] h-[18px]" />
          ) : (
            <Sun className="w-[18px] h-[18px]" />
          )}
          {light ? "dark_mode" : "light_mode"}
        </button>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-ink-500 hover:text-red-400 hover:bg-red-500/5 transition-colors"
        >
          <LogOut className="w-[18px] h-[18px]" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
