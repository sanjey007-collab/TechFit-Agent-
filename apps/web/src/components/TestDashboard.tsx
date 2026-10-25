import React, { useState } from "react";
import { ShieldCheck, Play, CheckCircle2, XCircle, Clock, Terminal, ChevronDown, ChevronUp } from "lucide-react";
import type { TestRunSummary, TestRunItem } from "../types";
import { runOfficialTests } from "../api";

export const TestDashboard: React.FC = () => {
  const [summary, setSummary] = useState<TestRunSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>("TC1");

  const handleRunAll = async () => {
    setRunning(true);
    try {
      const res = await runOfficialTests();
      setSummary(res);
      if (res.test_results.length > 0) {
        setExpandedId(res.test_results[0].test_case_id);
      }
    } catch (err) {
      alert(`Test execution failed: ${err}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                Official Hackathon Verification Suite
              </h2>
            </div>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Executes the four mandatory official test cases (TC1-TC4) directly through the real backend agent pipeline, rule engines, and independent verifier. <strong>Never hardcoded</strong>.
            </p>
          </div>

          <button
            onClick={handleRunAll}
            disabled={running}
            className="px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm shadow-md transition disabled:opacity-50 flex items-center space-x-2 w-full sm:w-auto justify-center"
          >
            {running ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Executing Automated Suite...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run All Official Tests</span>
              </>
            )}
          </button>
        </div>

        {/* Live Summary Bar if tests were run */}
        {summary && (
          <div className="mt-6 pt-6 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <span className="text-[11px] font-bold uppercase text-slate-400">Total Cases</span>
              <div className="text-xl font-black text-slate-800">{summary.total_tests}</div>
            </div>
            <div className="bg-emerald-50 p-3.5 rounded-xl border border-emerald-200">
              <span className="text-[11px] font-bold uppercase text-emerald-700">Passed</span>
              <div className="text-xl font-black text-emerald-800">{summary.passed_tests}</div>
            </div>
            <div className={`p-3.5 rounded-xl border ${summary.failed_tests > 0 ? "bg-rose-50 border-rose-200" : "bg-slate-50 border-slate-200"}`}>
              <span className={`text-[11px] font-bold uppercase ${summary.failed_tests > 0 ? "text-rose-700" : "text-slate-400"}`}>Failed</span>
              <div className={`text-xl font-black ${summary.failed_tests > 0 ? "text-rose-800" : "text-slate-400"}`}>{summary.failed_tests}</div>
            </div>
            <div className="bg-indigo-50 p-3.5 rounded-xl border border-indigo-200">
              <span className="text-[11px] font-bold uppercase text-indigo-700">Suite Status</span>
              <div className="text-base font-black text-indigo-900 truncate">{summary.overall_status}</div>
            </div>
          </div>
        )}
      </div>

      {/* Official Cases Accordion */}
      <div className="space-y-4">
        {summary ? (
          summary.test_results.map((t) => {
            const isPass = t.pass_fail === "PASS";
            const isExpanded = expandedId === t.test_case_id;

            return (
              <div
                key={t.test_case_id}
                className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden transition"
              >
                <div
                  onClick={() => setExpandedId(isExpanded ? null : t.test_case_id)}
                  className="p-5 flex items-center justify-between cursor-pointer hover:bg-slate-50 select-none"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs ${
                      isPass ? "bg-emerald-600" : "bg-rose-600"
                    }`}>
                      {isPass ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                          {t.test_case_id}
                        </span>
                        <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                          {t.test_name}
                        </h3>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{t.input_summary}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right hidden sm:block">
                      <span className={`text-xs font-black px-2.5 py-1 rounded-full ${
                        isPass ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                      }`}>
                        {t.pass_fail}
                      </span>
                      <span className="block text-[11px] text-slate-400 font-mono mt-1">
                        {t.duration_ms} ms
                      </span>
                    </div>
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-100 bg-slate-50/50 space-y-4 text-xs">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="bg-white p-3 rounded-xl border border-slate-200">
                        <span className="text-[10px] font-bold uppercase text-slate-400">Verdict Assertion</span>
                        <div className="mt-1 flex items-center space-x-2 font-medium">
                          <span className="text-slate-500">Expected:</span>
                          <span className="font-bold text-slate-800">{t.expected_verdict}</span>
                          <span className="text-slate-400">|</span>
                          <span className="text-slate-500">Actual:</span>
                          <span className="font-bold text-slate-900">{t.actual_verdict}</span>
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded-xl border border-slate-200">
                        <span className="text-[10px] font-bold uppercase text-slate-400">Cart Mutation Assertion</span>
                        <div className="mt-1 font-medium text-slate-800">
                          {t.actual_cart_status}
                        </div>
                      </div>
                    </div>

                    {/* Step-by-step Audit Logs */}
                    <div>
                      <div className="flex items-center space-x-1.5 text-slate-600 font-bold mb-1.5">
                        <Terminal className="w-3.5 h-3.5" />
                        <span>Execution Trace & Verifier Log</span>
                      </div>
                      <div className="bg-slate-900 text-emerald-400 font-mono p-3 rounded-xl text-[11px] overflow-x-auto space-y-1">
                        {t.logs.map((log, lIdx) => (
                          <div key={lIdx}>&gt; {log}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400">
            <Clock className="w-10 h-10 mx-auto text-slate-300 mb-2" />
            <p className="text-sm font-medium">No test run recorded yet.</p>
            <p className="text-xs text-slate-400 mt-1">Click "Run All Official Tests" above to execute all 4 fixtures live.</p>
          </div>
        )}
      </div>
    </div>
  );
};
