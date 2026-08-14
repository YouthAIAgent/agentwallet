import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import Brand from "../components/Brand";
import { auth, setToken } from "../api";

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let res;
      if (isRegister) {
        res = await auth.register({
          email,
          password,
          org_name: orgName,
        });
      } else {
        res = await auth.login({ email, password });
      }
      setToken(res.access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink-950 px-4 relative overflow-hidden">
      {/* Subtle grid backdrop */}
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      {/* Emerald glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[520px] h-[420px] bg-brand-500/5 blur-3xl rounded-full pointer-events-none" />

      <div className="relative w-full max-w-md">
        {/* Brand header */}
        <div className="mb-8">
          <div className="flex justify-center">
            <Brand size="lg" tagline="Solana Protocol" center />
          </div>
          <div className="mt-5 flex justify-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 border border-ink-800 bg-ink-900 rounded text-[11px] text-ink-400">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
              devnet · api connected
            </div>
          </div>
        </div>

        {/* Auth card */}
        <div className="card !p-0 overflow-hidden">
          {/* Terminal strip */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink-800 bg-ink-900/80">
            <span className="text-[11px] text-ink-500 uppercase tracking-widest">
              {isRegister ? "register.sh" : "login.sh"}
            </span>
            <span className="text-[11px] text-ink-500">
              {isRegister ? "create org" : "existing session"}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {isRegister && (
              <div>
                <label htmlFor="orgName" className="label">
                  Organization Name
                </label>
                <input
                  id="orgName"
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="input"
                  placeholder="Acme Corp"
                  required
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="label">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@company.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Enter your password"
                required
                minLength={8}
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded px-4 py-3">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {isRegister ? "create_account" : "sign_in"}
            </button>
          </form>

          <div className="mt-0 px-6 pb-6 pt-4 border-t border-ink-800 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
              className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
            >
              {isRegister
                ? "already registered? sign_in"
                : "new org? register"}
            </button>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-ink-600 mt-6">
          agentwallet v0.4.x · agent-genesis · mainnet soon
        </p>
      </div>
    </div>
  );
}
