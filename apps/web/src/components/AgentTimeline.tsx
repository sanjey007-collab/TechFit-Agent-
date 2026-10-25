import React from "react";
import { Check, Search, FileText, CheckCircle2, ShieldAlert, ShoppingBag, Eye } from "lucide-react";

interface AgentTimelineProps {
  currentStep: number; // 1 to 7
  statusText: string;
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ currentStep, statusText }) => {
  const steps = [
    { num: 1, label: "Identify", desc: "Resolve hardware variant", icon: Search },
    { num: 2, label: "Retrieve", desc: "Fetch official specs", icon: FileText },
    { num: 3, label: "Validate", desc: "Conflict detection", icon: ShieldAlert },
    { num: 4, label: "Compare", desc: "Deterministic rules", icon: CheckCircle2 },
    { num: 5, label: "Explain", desc: "Grounded rationale", icon: Check },
    { num: 6, label: "Approve", desc: "Human in the loop", icon: ShoppingBag },
    { num: 7, label: "Verify", desc: "Independent cart read", icon: Eye },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Agent Execution Pipeline
        </span>
        <span className="text-xs font-medium text-sky-700 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-200">
          {statusText || "Ready for analysis"}
        </span>
      </div>

      <div className="grid grid-cols-7 gap-1 sm:gap-2">
        {steps.map((s) => {
          const Icon = s.icon;
          const isDone = currentStep > s.num;
          const isCurrent = currentStep === s.num;
          const isPending = currentStep < s.num;

          return (
            <div key={s.num} className="flex flex-col items-center text-center">
              <div
                className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center transition-all ${
                  isDone
                    ? "bg-emerald-600 text-white shadow-sm"
                    : isCurrent
                    ? "bg-sky-600 text-white ring-4 ring-sky-100 shadow-md animate-pulse"
                    : "bg-slate-100 text-slate-400 border border-slate-200"
                }`}
              >
                <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <span className={`text-[11px] sm:text-xs font-semibold mt-1.5 ${
                isCurrent ? "text-sky-700 font-bold" : isDone ? "text-slate-800" : "text-slate-400"
              }`}>
                {s.label}
              </span>
              <span className="text-[9px] text-slate-400 hidden lg:inline">
                {s.desc}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
