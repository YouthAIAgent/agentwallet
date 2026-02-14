import { useEffect, useState } from "react";
import {
  KeyRound,
  Plus,
  X,
  Loader2,
  Copy,
  Eye,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ArrowLeft,
} from "lucide-react";
import {
  pdaWallets,
  wallets,
  type PdaWallet,
  type CreatePdaWalletRequest,
  type PdaOnChainState,
  type Wallet,
} from "../api";

const mockPdaWallets: PdaWallet[] = [
  {
    id: "pda_01",
    organization_id: "org_01",
    authority_wallet_id: "w_03",
    agent_id_seed: "trading-bot-alpha",
    pda_address: "5xKXqv9mNpL3yR5tU2wE8sD4fGhJ6kBnC1aZoYiPDA1",
    spending_limit_per_tx: "0.5",
    daily_limit: "5.0",
    is_active: true,
    created_at: "2026-02-10T10:00:00Z",
    updated_at: "2026-02-11T08:00:00Z",
  },
  {
    id: "pda_02",
    organization_id: "org_01",
    authority_wallet_id: "w_03",
    agent_id_seed: "payment-agent",
    pda_address: "8yMNqw2rOpK4zS6uV3xF9tE5gIhL7jCmD2bAqZiPDA2",
    spending_limit_per_tx: "1.0",
    daily_limit: "10.0",
    is_active: true,
    created_at: "2026-02-11T14:30:00Z",
    updated_at: "2026-02-11T14:30:00Z",
  },
  {
    id: "pda_03",
    organization_id: "org_01",
    authority_wallet_id: "w_03",
    agent_id_seed: "staking-manager",
    pda_address: "3wJKpv7nRsH2xQ4tS1yD8uF6gBhI9jAlE5cMoXiPDA3",
    spending_limit_per_tx: "2.0",
    daily_limit: "20.0",
    is_active: false,
    created_at: "2026-02-08T09:00:00Z",
    updated_at: "2026-02-12T12:00:00Z",
  },
];

function truncateAddress(addr: string): string {
  if (addr.length <= 16) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-6)}`;
}

type ViewMode = "list" | "detail" | "derive";

export default function PdaWallets() {
  // List state
  const [pdaList, setPdaList] = useState<PdaWallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedAddr, setCopiedAddr] = useState<string | null>(null);

  // Create modal state
  const [showCreate, setShowCreate] = useState(false);
  const [walletOptions, setWalletOptions] = useState<Wallet[]>([]);
  const [formData, setFormData] = useState<CreatePdaWalletRequest>({
    authority_wallet_id: "",
    agent_id_seed: "",
    spending_limit_per_tx: 0.5,
    daily_limit: 5.0,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Detail view state
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedPda, setSelectedPda] = useState<PdaWallet | null>(null);
  const [onChainState, setOnChainState] = useState<PdaOnChainState | null>(null);
  const [stateLoading, setStateLoading] = useState(false);
  const [stateError, setStateError] = useState("");

  // Derive state
  const [deriveOrgPubkey, setDeriveOrgPubkey] = useState("");
  const [deriveAgentSeed, setDeriveAgentSeed] = useState("");
  const [derivedAddress, setDerivedAddress] = useState<string | null>(null);
  const [derivedBump, setDerivedBump] = useState<number | null>(null);
  const [deriveLoading, setDeriveLoading] = useState(false);
  const [deriveError, setDeriveError] = useState("");

  useEffect(() => {
    pdaWallets
      .list()
      .then((res) => setPdaList(res.pda_wallets))
      .catch(() => setPdaList(mockPdaWallets))
      .finally(() => setLoading(false));
  }, []);

  // Load wallets for the authority dropdown when create modal opens
  useEffect(() => {
    if (showCreate) {
      wallets
        .list({ limit: 100 })
        .then((res) => setWalletOptions(res.wallets))
        .catch(() => setWalletOptions([]));
    }
  }, [showCreate]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const pda = await pdaWallets.create(formData);
      setPdaList((prev) => [pda, ...prev]);
      closeCreateModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create PDA wallet");
    } finally {
      setSubmitting(false);
    }
  };

  const closeCreateModal = () => {
    setShowCreate(false);
    setFormData({
      authority_wallet_id: "",
      agent_id_seed: "",
      spending_limit_per_tx: 0.5,
      daily_limit: 5.0,
    });
    setError("");
  };

  const copyAddress = async (addr: string) => {
    await navigator.clipboard.writeText(addr);
    setCopiedAddr(addr);
    setTimeout(() => setCopiedAddr(null), 2000);
  };

  const openDetail = (pda: PdaWallet) => {
    setSelectedPda(pda);
    setOnChainState(null);
    setStateError("");
    setViewMode("detail");
  };

  const fetchOnChainState = async () => {
    if (!selectedPda) return;
    setStateLoading(true);
    setStateError("");
    try {
      const state = await pdaWallets.getState(selectedPda.id);
      setOnChainState(state);
    } catch (err) {
      setStateError(
        err instanceof Error ? err.message : "Failed to read on-chain state"
      );
    } finally {
      setStateLoading(false);
    }
  };

  const handleDerive = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeriveLoading(true);
    setDeriveError("");
    setDerivedAddress(null);
    setDerivedBump(null);
    try {
      const res = await pdaWallets.derive({
        org_pubkey: deriveOrgPubkey,
        agent_id_seed: deriveAgentSeed,
      });
      setDerivedAddress(res.pda_address);
      setDerivedBump(res.bump);
    } catch (err) {
      setDeriveError(
        err instanceof Error ? err.message : "Failed to derive PDA address"
      );
    } finally {
      setDeriveLoading(false);
    }
  };

  const backToList = () => {
    setViewMode("list");
    setSelectedPda(null);
    setOnChainState(null);
    setStateError("");
  };

  const activeCount = pdaList.filter((p) => p.is_active).length;
  const totalLimit = pdaList.reduce(
    (sum, p) => sum + parseFloat(p.daily_limit || "0"),
    0
  );

  // --- Detail View ---
  if (viewMode === "detail" && selectedPda) {
    return (
      <div>
        <button
          onClick={backToList}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to PDA Wallets
        </button>

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">PDA Wallet Details</h1>
            <p className="text-slate-400 mt-1 text-sm font-mono">
              {selectedPda.pda_address}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => copyAddress(selectedPda.pda_address)}
              className="btn-secondary"
            >
              {copiedAddr === selectedPda.pda_address ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Address
                </>
              )}
            </button>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Wallet Info
            </h3>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">ID</dt>
                <dd className="text-sm font-mono text-slate-200">{selectedPda.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Agent ID Seed</dt>
                <dd className="text-sm font-mono text-brand-400">
                  {selectedPda.agent_id_seed}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Authority Wallet</dt>
                <dd className="text-sm font-mono text-slate-200">
                  {selectedPda.authority_wallet_id}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Status</dt>
                <dd>
                  {selectedPda.is_active ? (
                    <span className="badge-green">Active</span>
                  ) : (
                    <span className="badge-red">Inactive</span>
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Created</dt>
                <dd className="text-sm text-slate-200">
                  {new Date(selectedPda.created_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Spending Limits
            </h3>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Per Transaction</dt>
                <dd className="text-sm font-mono text-slate-200">
                  {parseFloat(selectedPda.spending_limit_per_tx).toFixed(4)} SOL
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-slate-500">Daily Limit</dt>
                <dd className="text-sm font-mono text-slate-200">
                  {parseFloat(selectedPda.daily_limit).toFixed(4)} SOL
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* On-Chain State */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              On-Chain State
            </h3>
            <button
              onClick={fetchOnChainState}
              disabled={stateLoading}
              className="btn-secondary text-xs"
            >
              {stateLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              {onChainState ? "Refresh" : "Read State"}
            </button>
          </div>

          {stateError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 mb-4">
              <p className="text-sm text-red-400">{stateError}</p>
            </div>
          )}

          {onChainState ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">Authority</p>
                <p className="text-sm font-mono text-slate-200 break-all">
                  {truncateAddress(onChainState.authority)}
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">SOL Balance</p>
                <p className="text-lg font-mono font-bold text-emerald-400">
                  {onChainState.sol_balance.toFixed(4)} SOL
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">Active</p>
                <p className="flex items-center gap-2">
                  {onChainState.is_active ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-emerald-400">Yes</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-red-400" />
                      <span className="text-sm text-red-400">No</span>
                    </>
                  )}
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">Daily Spent</p>
                <p className="text-sm font-mono text-slate-200">
                  {onChainState.daily_spent.toFixed(4)} SOL
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">Daily Limit</p>
                <p className="text-sm font-mono text-slate-200">
                  {onChainState.daily_limit.toFixed(4)} SOL
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-xs text-slate-500 mb-1">Limit Per TX</p>
                <p className="text-sm font-mono text-slate-200">
                  {onChainState.spending_limit_per_tx.toFixed(4)} SOL
                </p>
              </div>
            </div>
          ) : !stateLoading ? (
            <div className="flex flex-col items-center justify-center py-10 text-slate-500">
              <Search className="w-8 h-8 mb-2" />
              <p className="text-sm">
                Click "Read State" to fetch live on-chain data
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
            </div>
          )}
        </div>
      </div>
    );
  }

  // --- Derive View ---
  if (viewMode === "derive") {
    return (
      <div>
        <button
          onClick={backToList}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to PDA Wallets
        </button>

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Derive PDA Address</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Compute a Program Derived Address from an organization public key and agent
            seed
          </p>
        </div>

        <div className="card max-w-xl">
          <form onSubmit={handleDerive} className="space-y-5">
            <div>
              <label htmlFor="deriveOrgPubkey" className="label">
                Organization Public Key
              </label>
              <input
                id="deriveOrgPubkey"
                type="text"
                value={deriveOrgPubkey}
                onChange={(e) => setDeriveOrgPubkey(e.target.value)}
                className="input font-mono"
                placeholder="Enter Solana public key..."
                required
              />
            </div>
            <div>
              <label htmlFor="deriveAgentSeed" className="label">
                Agent ID Seed
              </label>
              <input
                id="deriveAgentSeed"
                type="text"
                value={deriveAgentSeed}
                onChange={(e) => setDeriveAgentSeed(e.target.value)}
                className="input"
                placeholder="e.g. trading-bot-alpha"
                required
              />
            </div>

            {deriveError && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
                <p className="text-sm text-red-400">{deriveError}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={deriveLoading}
              className="btn-primary w-full"
            >
              {deriveLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Derive Address
            </button>
          </form>

          {derivedAddress && (
            <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
              <div>
                <p className="text-xs text-slate-500 mb-1">Derived PDA Address</p>
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono text-brand-400 break-all">
                    {derivedAddress}
                  </code>
                  <button
                    onClick={() => copyAddress(derivedAddress)}
                    className="p-1 text-slate-600 hover:text-slate-400 transition-colors flex-shrink-0"
                  >
                    {copiedAddr === derivedAddress ? (
                      <span className="text-emerald-400 text-[10px] font-medium">
                        Copied
                      </span>
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
              {derivedBump !== null && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Bump Seed</p>
                  <code className="text-sm font-mono text-slate-200">
                    {derivedBump}
                  </code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // --- List View ---
  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">PDA Wallets</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Solana Program Derived Address wallets for autonomous agents
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode("derive")}
            className="btn-secondary"
          >
            <Search className="w-4 h-4" />
            Derive Address
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
            Create PDA Wallet
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <div className="card">
          <p className="text-sm text-slate-400">Total PDA Wallets</p>
          <p className="text-2xl font-bold text-white mt-1">{pdaList.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">Active</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{activeCount}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">Total Daily Limit</p>
          <p className="text-2xl font-bold text-white mt-1">
            {totalLimit.toFixed(2)} SOL
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : pdaList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <KeyRound className="w-10 h-10 mb-3" />
            <p className="text-sm font-medium">No PDA wallets yet</p>
            <p className="text-xs mt-1">
              Create your first PDA wallet to get started
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="table-header">PDA Address</th>
                <th className="table-header">Agent Seed</th>
                <th className="table-header">Limit / TX</th>
                <th className="table-header">Daily Limit</th>
                <th className="table-header">Status</th>
                <th className="table-header">Created</th>
                <th className="table-header text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {pdaList.map((pda) => (
                <tr
                  key={pda.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono text-slate-400">
                        {truncateAddress(pda.pda_address)}
                      </code>
                      <button
                        onClick={() => copyAddress(pda.pda_address)}
                        className="p-1 text-slate-600 hover:text-slate-400 transition-colors"
                      >
                        {copiedAddr === pda.pda_address ? (
                          <span className="text-emerald-400 text-[10px] font-medium">
                            Copied
                          </span>
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className="text-sm font-mono text-brand-400">
                      {pda.agent_id_seed}
                    </span>
                  </td>
                  <td className="table-cell">
                    <span className="font-mono text-sm text-slate-200">
                      {parseFloat(pda.spending_limit_per_tx).toFixed(2)} SOL
                    </span>
                  </td>
                  <td className="table-cell">
                    <span className="font-mono text-sm text-slate-200">
                      {parseFloat(pda.daily_limit).toFixed(2)} SOL
                    </span>
                  </td>
                  <td className="table-cell">
                    {pda.is_active ? (
                      <span className="badge-green">Active</span>
                    ) : (
                      <span className="badge-red">Inactive</span>
                    )}
                  </td>
                  <td className="table-cell text-xs text-slate-500">
                    {new Date(pda.created_at).toLocaleDateString()}
                  </td>
                  <td className="table-cell text-right">
                    <button
                      onClick={() => openDetail(pda)}
                      className="p-1.5 rounded-md text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
                      title="View details"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
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
                Create PDA Wallet
              </h2>
              <button
                onClick={closeCreateModal}
                className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-5">
              <div>
                <label htmlFor="authorityWallet" className="label">
                  Authority Wallet
                </label>
                {walletOptions.length > 0 ? (
                  <select
                    id="authorityWallet"
                    value={formData.authority_wallet_id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        authority_wallet_id: e.target.value,
                      })
                    }
                    className="input"
                    required
                  >
                    <option value="">Select a wallet...</option>
                    {walletOptions.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.label || w.id} ({w.chain} - {truncateAddress(w.address)})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    id="authorityWallet"
                    type="text"
                    value={formData.authority_wallet_id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        authority_wallet_id: e.target.value,
                      })
                    }
                    className="input"
                    placeholder="w_..."
                    required
                  />
                )}
                <p className="text-xs text-slate-500 mt-1">
                  The Solana wallet that will serve as authority for this PDA
                </p>
              </div>
              <div>
                <label htmlFor="agentIdSeed" className="label">
                  Agent ID Seed
                </label>
                <input
                  id="agentIdSeed"
                  type="text"
                  value={formData.agent_id_seed}
                  onChange={(e) =>
                    setFormData({ ...formData, agent_id_seed: e.target.value })
                  }
                  className="input"
                  placeholder="e.g. trading-bot-alpha"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Unique seed string used to derive the PDA address
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="spendingLimitPerTx" className="label">
                    Limit Per TX (SOL)
                  </label>
                  <input
                    id="spendingLimitPerTx"
                    type="number"
                    step="0.0001"
                    min="0"
                    value={formData.spending_limit_per_tx}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        spending_limit_per_tx: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="dailyLimit" className="label">
                    Daily Limit (SOL)
                  </label>
                  <input
                    id="dailyLimit"
                    type="number"
                    step="0.0001"
                    min="0"
                    value={formData.daily_limit}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        daily_limit: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="input"
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeCreateModal}
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
                  Create PDA Wallet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
