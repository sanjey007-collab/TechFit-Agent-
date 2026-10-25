import React, { useState } from "react";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  ExternalLink,
  ShoppingBag,
  Check,
  RotateCcw,
  Eye,
  FileText
} from "lucide-react";
import type { CompatibilityReport, CompatibilityVerdict, RuleStatus } from "../types";

interface ReportViewProps {
  report: CompatibilityReport;
  onApprove: (proposalId: string, sku: string, version: number) => Promise<void>;
  onClarify: (checkId: string, model: string) => Promise<void>;
  approving: boolean;
  onReset: () => void;
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  onApprove,
  onClarify,
  approving,
  onReset
}) => {
  const [clarifyInput, setClarifyInput] = useState("");
  const [clarifying, setClarifying] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);

  const getVerdictBadge = (verdict: CompatibilityVerdict) => {
    switch (verdict) {
      case "COMPATIBLE":
        return {
          bg: "bg-emerald-50 border-emerald-300 text-emerald-900",
          icon: CheckCircle,
          label: "COMPATIBLE",
          sub: "Verified Hardware Requirements Satisfied"
        };
      case "INCOMPATIBLE":
        return {
          bg: "bg-rose-50 border-rose-300 text-rose-900",
          icon: XCircle,
          label: "INCOMPATIBLE",
          sub: "Hard Technical Constraint Mismatch"
        };
      case "UNCERTAIN":
        return {
          bg: "bg-amber-50 border-amber-300 text-amber-900",
          icon: AlertTriangle,
          label: "UNCERTAIN",
          sub: "Contradictory Manufacturer Claims or Incomplete Data"
        };
      case "MORE_INFO_REQUIRED":
        return {
          bg: "bg-indigo-50 border-indigo-300 text-indigo-900",
          icon: HelpCircle,
          label: "MORE INFO REQUIRED",
          sub: "Ambiguous Device Identity Resolution"
        };
      case "NOT_TRUSTED":
        return {
          bg: "bg-orange-50 border-orange-300 text-orange-900",
          icon: ShieldAlert,
          label: "NOT TRUSTED",
          sub: "Unsubstantiated Seller 'Universal' Claim Without Evidence"
        };
    }
  };

  const badge = getVerdictBadge(report.verdict);
  const Icon = badge.icon;

  const handleClarifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarifyInput.trim()) return;
    setClarifying(true);
    try {
      await onClarify(report.check_id, clarifyInput.trim());
      setClarifyInput("");
    } finally {
      setClarifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Main Verdict Header Card */}
      <div className={`border rounded-2xl p-6 sm:p-8 shadow-sm ${badge.bg}`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-white/80 rounded-2xl shadow-sm border border-black/5 mt-0.5">
              <Icon className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-black/10">
                  {badge.label}
                </span>
                <span className="text-xs text-slate-500 font-mono">ID: {report.check_id}</span>
              </div>
              <h2 className="text-2xl font-black tracking-tight mt-1">
                {report.verdict_summary}
              </h2>
              <p className="text-sm opacity-90 mt-1 max-w-2xl">
                {report.detailed_explanation}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            {report.proposal && report.proposal.status === "AWAITING_APPROVAL" && (
              <button
                onClick={() => setShowApprovalModal(true)}
                className="w-full sm:w-auto px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition flex items-center justify-center space-x-2"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>Review Cart Proposal</span>
              </button>
            )}
            <button
              onClick={onReset}
              className="px-4 py-3 rounded-xl bg-white/80 hover:bg-white text-slate-700 font-semibold text-sm border border-slate-300 transition flex items-center space-x-1.5"
            >
              <RotateCcw className="w-4 h-4" />
              <span>New Check</span>
            </button>
          </div>
        </div>

        {/* Verification receipt banner if already verified */}
        {report.verification && (
          <div className="mt-5 pt-4 border-t border-black/10 flex items-center space-x-3 text-xs">
            <span className={`px-2 py-0.5 rounded font-bold ${
              report.verification.status === "VERIFIED" ? "bg-emerald-200 text-emerald-900" : "bg-rose-200 text-rose-900"
            }`}>
              {report.verification.status}
            </span>
            <span className="font-medium text-slate-700">
              {report.verification.details}
            </span>
          </div>
        )}
      </div>

      {/* 2. Clarification Prompt (for MORE_INFO_REQUIRED or UNCERTAIN) */}
      {(report.verdict === "MORE_INFO_REQUIRED" || report.verdict === "UNCERTAIN") && (
        <div className="bg-white border-2 border-indigo-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-start space-x-3 mb-4">
            <HelpCircle className="w-6 h-6 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-slate-900 text-base">
                Precise Hardware Identifier Required
              </h3>
              <p className="text-sm text-slate-600 mt-1">
                {report.next_action_instructions}
              </p>
              <div className="mt-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <strong>Where to find it:</strong> Check the sticker label on the bottom of the laptop chassis, press F2 on boot to open BIOS, or check Dell SupportAssist / Lenovo Vantage.
              </div>
            </div>
          </div>

          <form onSubmit={handleClarifySubmit} className="flex gap-3">
            <input
              type="text"
              required
              value={clarifyInput}
              onChange={(e) => setClarifyInput(e.target.value)}
              placeholder="e.g. DEMO-LAPTOP-001 or Inspiron 15 3520"
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={clarifying || !clarifyInput.trim()}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm transition disabled:opacity-50"
            >
              {clarifying ? "Resuming Check..." : "Submit Model Details"}
            </button>
          </form>
        </div>
      )}

      {/* 3. Deterministic Specification Comparison Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-slate-900 text-sm sm:text-base">
              Deterministic Hardware Rule Comparisons
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated strictly by pure rule functions without LLM hallucination risk.
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-200 text-slate-700 rounded-lg">
            {report.comparisons.length} rules evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100/75 text-slate-600 text-[11px] uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Rule / Property</th>
                <th className="px-6 py-3">Device Required</th>
                <th className="px-6 py-3">Candidate Observed</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Technical Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {report.comparisons.map((c, idx) => {
                const isPass = c.status === "PASS";
                const isFail = c.status === "FAIL";
                return (
                  <tr key={idx} className="hover:bg-slate-50/50 transition">
                    <td className="px-6 py-3.5 font-semibold text-slate-900">
                      {c.rule_name}
                      <span className="block text-[11px] text-slate-400 font-mono">{c.field_name}</span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-700 font-medium">
                      {c.required_value}
                    </td>
                    <td className="px-6 py-3.5 text-slate-700 font-medium">
                      {c.observed_value}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                        isPass
                          ? "bg-emerald-100 text-emerald-800"
                          : isFail
                          ? "bg-rose-100 text-rose-800"
                          : "bg-amber-100 text-amber-800"
                      }`}>
                        {isPass ? <Check className="w-3 h-3" /> : isFail ? <XCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                        <span>{c.status}</span>
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-600 text-xs">
                      {c.explanation}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Traceable Evidence & Citations Drawer */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h3 className="font-bold text-slate-900 text-base mb-1 flex items-center space-x-2">
          <FileText className="w-4 h-4 text-sky-600" />
          <span>Authoritative Evidence & Provenance</span>
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          All extracted facts were verified against verbatim manufacturer documentation excerpts.
        </p>

        {report.evidence_items.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No external document records attached to this check.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.evidence_items.map((src, idx) => (
              <div key={idx} className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-sky-800 bg-sky-100 px-2 py-0.5 rounded">
                      {src.is_official ? "Official Manufacturer PSREF" : "Marketplace Listing"}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {new Date(src.retrieval_timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm mt-2 line-clamp-1">
                    {src.title}
                  </h4>
                  <div className="mt-2 bg-white p-2.5 rounded-lg border border-slate-200 text-xs text-slate-600 italic">
                    "{src.excerpt}"
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-mono text-[11px] truncate max-w-[200px]">
                    {src.domain}
                  </span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sky-600 hover:text-sky-800 font-semibold flex items-center space-x-1"
                  >
                    <span>View Source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Human Approval Modal */}
      {showApprovalModal && report.proposal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center space-x-3 text-emerald-600 mb-4">
              <ShoppingBag className="w-6 h-6" />
              <h3 className="text-xl font-bold text-slate-900">
                Explicit Human Cart Approval
              </h3>
            </div>

            <p className="text-sm text-slate-600 mb-6">
              The AI agent verified hardware compatibility but requires your explicit authorization before adding this item to the mock cart.
            </p>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2.5 mb-6 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Proposed Product:</span>
                <span className="font-bold text-slate-900">{report.proposal.product_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">SKU:</span>
                <span className="font-mono font-semibold text-slate-800">{report.proposal.product_sku}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Quantity:</span>
                <span className="font-semibold text-slate-800">{report.proposal.quantity} unit</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Price:</span>
                <span className="font-bold text-emerald-700">${report.proposal.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Destination Cart:</span>
                <span className="font-mono text-slate-600">{report.proposal.cart_id}</span>
              </div>
              <div className="pt-2 border-t border-slate-200 text-xs text-slate-500">
                <strong>Agent Rationale:</strong> {report.proposal.rationale}
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={() => setShowApprovalModal(false)}
                className="flex-1 py-3 rounded-xl border border-slate-300 font-semibold text-slate-700 hover:bg-slate-50 text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={approving}
                onClick={async () => {
                  if (report.proposal) {
                    await onApprove(
                      report.proposal.proposal_id,
                      report.proposal.product_sku,
                      report.proposal.version
                    );
                    setShowApprovalModal(false);
                  }
                }}
                className="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {approving ? (
                  <span>Executing & Verifying...</span>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Approve & Add to Cart</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
