import React, { useEffect, useState } from "react";
import { History, Eye, ArrowRight } from "lucide-react";
import type { CompatibilityReport } from "../types";
import { fetchRecentChecks } from "../api";

interface HistoryViewProps {
  onSelectReport: (report: CompatibilityReport) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({ onSelectReport }) => {
  const [reports, setReports] = useState<CompatibilityReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentChecks()
      .then((data) => setReports(data))
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-slate-200">
        <div className="p-2 bg-slate-100 text-slate-700 rounded-lg">
          <History className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Audit History & Past Analyses</h2>
          <p className="text-xs text-slate-500">Every check, rule result, and cart mutation is immutably logged for auditability.</p>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">Loading audit logs...</div>
      ) : reports.length === 0 ? (
        <div className="py-12 text-center text-slate-400 text-sm">No analysis history found. Run a check to begin.</div>
      ) : (
        <div className="divide-y divide-slate-100">
          {reports.map((r) => (
            <div key={r.check_id} className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:bg-slate-50/50 p-2 rounded-xl transition">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900 text-sm">
                    {r.resolved_device_brand || "Device"} {r.resolved_device_model || r.check_id}
                  </span>
                  <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
                    {r.part_type}
                  </span>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                    r.verdict === "COMPATIBLE"
                      ? "bg-emerald-100 text-emerald-800"
                      : r.verdict === "INCOMPATIBLE"
                      ? "bg-rose-100 text-rose-800"
                      : r.verdict === "UNCERTAIN"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-slate-100 text-slate-700"
                  }`}>
                    {r.verdict}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 line-clamp-1">{r.verdict_summary}</p>
                <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                  {new Date(r.created_at).toLocaleString()} | ID: {r.check_id}
                </span>
              </div>

              <button
                onClick={() => onSelectReport(r)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 flex items-center space-x-1"
              >
                <span>View Full Audit</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
