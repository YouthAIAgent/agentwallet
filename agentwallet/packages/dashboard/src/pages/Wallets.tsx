import { useEffect, useState } from "react";
import { Wallet as WalletIcon, Plus, X, Loader2, ExternalLink, Copy } from "lucide-react";
import { wallets, type Wallet, type CreateWalletRequest } from "../api";

const mockWallets: Wallet[] = [
  {
    id: "w_01",
    agent_id: "ag_01",
    chain: "ethereum",
    address: "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12",
    balance: "12.4500",
    status: "active",
    created_at: "2026-01-15T10:00:00Z",
    label: "Main Trading Wallet",
  },
  {
    id: "w_02",
    agent_id: "ag_02",
    chain: "polygon",
    address: "0x9876543210fedcba9876543210fedcba98765432",
    balance: "8250.00",
    status: "active",
    created_at: "2026-01-20T14:30:00Z",
    label: "Payment Disbursement",
  },
  {
    id: "w_03",
    agent_id: "ag_01",
    chain: "solana",
    address: "7xKXqv9mNpL3yR5tU2wE8sD4fGhJ6kBnC1aZoYiO",
    balance: "15420.50",
    status: "active",
    created_at: "2026-02-01T09:00:00Z",
    label: "Solana Operations",
  },
  {
    id: "w_04",
    agent_id: null,
    chain: "ethereum",
    address: "0xaabbccdd11223344556677889900aabbccddeeff",
    balance: "0.0000",
    status: "frozen",
    created_at: "2025-12-05T18:00:00Z",
    label: "Legacy Vault",
  },
  {
    id: "w_05",
    agent_id: "ag_05",
    chain: "arbitrum",
    address: "0x1122334455667788990011223344556677889900",
    balance: "3780.25",
    status: "active",
    created_at: "2026-02-05T11:00:00Z",
    label: "Bridge Relay Fund",
  },
];

const chainBadge = (chain: string) => {
  const colors: Record<string, string> = {
    ethereum: "badge-blue",
    polygon: "badge bg-purple-500/10 text-purple-400 border border-purple-500/20",
    solana: "badge bg-teal-500/10 text-teal-400 border border-teal-500/20",
    arbitrum: "badge-blue",
    base: "badge-blue",
  };
  return (
    <span className={colors[chain] || "badge-gray"}>
      {chain.charAt(0).toUpperCase() + chain.slice(1)}
    </span>
  );
};

const statusBadge = (status: string) => {
  switch (status) {
    case "active":
      return <span className="badge-green">Active</span>;
    case "frozen":
      return <span className="badge-yellow">Frozen</span>;
    case "archived":
      return <span className="badge-gray">Archived</span>;
    default:
      return <span className="badge-gray">{status}</span>;
  }
};

function truncateAddress(addr: string): string {
  if (addr.length <= 16) return addr;
  return `${addr.slice(0, 8)}...${addr.slice(-6)}`;
}

export default function Wallets() {
  const [walletList, setWalletList] = useState<Wallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState<CreateWalletRequest & { label: string }>({
    chain: "ethereum",
    agent_id: "",
    label: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [copiedAddr, setCopiedAddr] = useState<string | null>(null);

  useEffect(() => {
    wallets
      .list()
      .then((res) => setWalletList(res.wallets))
      .catch(() => setWalletList(mockWallets))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const wallet = await wallets.create({
        chain: formData.chain,
        agent_id: formData.agent_id || undefined,
        label: formData.label || undefined,
      });
      setWalletList((prev) => [wallet, ...prev]);
      closeModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create wallet");
    } finally {
      setSubmitting(false);
    }
  };

  const copyAddress = async (addr: string) => {
    await navigator.clipboard.writeText(addr);
    setCopiedAddr(addr);
    setTimeout(() => setCopiedAddr(null), 2000);
  };

  const closeModal = () => {
    setShowCreate(false);
    setFormData({ chain: "ethereum", agent_id: "", label: "" });
    setError("");
  };

  const totalBalance = walletList
    .filter((w) => w.chain === "ethereum" || w.chain === "arbitrum")
    .reduce((sum, w) => sum + parseFloat(w.balance || "0"), 0);

  const stablecoinBalance = walletList
    .filter((w) => w.chain === "polygon" || w.chain === "solana")
    .reduce((sum, w) => sum + parseFloat(w.balance || "0"), 0);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Wallets</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Manage custodial wallets across chains
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Create Wallet
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <div className="card">
          <p className="text-sm text-slate-400">Total Wallets</p>
          <p className="text-2xl font-bold text-white mt-1">{walletList.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">ETH Balance</p>
          <p className="text-2xl font-bold text-white mt-1">
            {totalBalance.toFixed(4)} ETH
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">Stablecoin Balance</p>
          <p className="text-2xl font-bold text-white mt-1">
            ${stablecoinBalance.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : walletList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <WalletIcon className="w-10 h-10 mb-3" />
            <p className="text-sm font-medium">No wallets yet</p>
            <p className="text-xs mt-1">Create your first wallet to get started</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="table-header">Label</th>
                <th className="table-header">Chain</th>
                <th className="table-header">Address</th>
                <th className="table-header">Balance</th>
                <th className="table-header">Status</th>
                <th className="table-header">Agent</th>
                <th className="table-header">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {walletList.map((wallet) => (
                <tr
                  key={wallet.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="table-cell">
                    <span className="font-medium text-slate-100">
                      {wallet.label || wallet.id}
                    </span>
                  </td>
                  <td className="table-cell">{chainBadge(wallet.chain)}</td>
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono text-slate-400">
                        {truncateAddress(wallet.address)}
                      </code>
                      <button
                        onClick={() => copyAddress(wallet.address)}
                        className="p-1 text-slate-600 hover:text-slate-400 transition-colors"
                      >
                        {copiedAddr === wallet.address ? (
                          <span className="text-emerald-400 text-[10px] font-medium">
                            Copied
                          </span>
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                      <a
                        href="#"
                        className="p-1 text-slate-600 hover:text-slate-400 transition-colors"
                        title="View on explorer"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className="font-mono text-sm text-slate-200">
                      {parseFloat(wallet.balance).toLocaleString()}
                    </span>
                  </td>
                  <td className="table-cell">{statusBadge(wallet.status)}</td>
                  <td className="table-cell">
                    {wallet.agent_id ? (
                      <span className="text-xs font-mono text-brand-400">
                        {wallet.agent_id}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-600">Unassigned</span>
                    )}
                  </td>
                  <td className="table-cell text-xs text-slate-500">
                    {new Date(wallet.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h2 className="text-lg font-semibold text-white">
                Create New Wallet
              </h2>
              <button
                onClick={closeModal}
                className="p-1 text-slate-500 hover:text-slate-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-5">
              <div>
                <label htmlFor="walletLabel" className="label">
                  Label
                </label>
                <input
                  id="walletLabel"
                  type="text"
                  value={formData.label}
                  onChange={(e) =>
                    setFormData({ ...formData, label: e.target.value })
                  }
                  className="input"
                  placeholder="Main Trading Wallet"
                />
              </div>
              <div>
                <label htmlFor="walletChain" className="label">
                  Blockchain
                </label>
                <select
                  id="walletChain"
                  value={formData.chain}
                  onChange={(e) =>
                    setFormData({ ...formData, chain: e.target.value })
                  }
                  className="input"
                >
                  <option value="ethereum">Ethereum</option>
                  <option value="polygon">Polygon</option>
                  <option value="arbitrum">Arbitrum</option>
                  <option value="base">Base</option>
                  <option value="solana">Solana</option>
                </select>
              </div>
              <div>
                <label htmlFor="walletAgent" className="label">
                  Assign to Agent (optional)
                </label>
                <input
                  id="walletAgent"
                  type="text"
                  value={formData.agent_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, agent_id: e.target.value })
                  }
                  className="input"
                  placeholder="ag_..."
                />
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary flex-1"
                >
                  {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  Create Wallet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
