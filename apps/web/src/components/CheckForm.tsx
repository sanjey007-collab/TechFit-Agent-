import React, { useState } from "react";
import { Search, Sparkles, AlertCircle, Laptop, Zap } from "lucide-react";
import type { PartType } from "../types";

interface CheckFormProps {
  onSubmit: (data: {
    device_brand?: string;
    device_model: string;
    part_type: PartType;
    ram_preferences?: { requested_capacity_gb?: number };
    candidate_sku?: string;
    natural_language_query?: string;
  }) => void;
  loading: boolean;
}

export const CheckForm: React.FC<CheckFormProps> = ({ onSubmit, loading }) => {
  const [deviceBrand, setDeviceBrand] = useState("");
  const [deviceModel, setDeviceModel] = useState("DEMO-LAPTOP-001");
  const [partType, setPartType] = useState<PartType>("RAM");
  const [requestedCapacity, setRequestedCapacity] = useState<number>(16);
  const [candidateSku, setCandidateSku] = useState("");
  const [nlQuery, setNlQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      device_brand: deviceBrand.trim() || undefined,
      device_model: deviceModel.trim(),
      part_type: partType,
      ram_preferences: partType === "RAM" ? { requested_capacity_gb: requestedCapacity } : undefined,
      candidate_sku: candidateSku.trim() || undefined,
      natural_language_query: nlQuery.trim() || undefined
    });
  };

  const setOfficialFixture = (tc: number) => {
    if (tc === 1) {
      setDeviceBrand("DemoTech");
      setDeviceModel("DEMO-LAPTOP-001");
      setPartType("RAM");
      setRequestedCapacity(16);
      setCandidateSku("RAM-A");
      setNlQuery("Find a compatible 16 GB DDR4 upgrade for my DEMO-LAPTOP-001");
    } else if (tc === 2) {
      setDeviceBrand("DemoTech");
      setDeviceModel("DEMO-LAPTOP-002");
      setPartType("RAM");
      setRequestedCapacity(16);
      setCandidateSku("");
      setNlQuery("Check if 16GB RAM upgrade works on DEMO-LAPTOP-002 with conflicting bulletins");
    } else if (tc === 3) {
      setDeviceBrand("Dell");
      setDeviceModel("Dell laptop");
      setPartType("RAM");
      setRequestedCapacity(8);
      setCandidateSku("");
      setNlQuery("I want 8GB RAM for my Dell laptop");
    } else if (tc === 4) {
      setDeviceBrand("DemoTech");
      setDeviceModel("DEMO-LAPTOP-004");
      setPartType("CHARGER");
      setCandidateSku("UNIVERSAL-CHARGER-001");
      setNlQuery("Will the Universal Multi-Tip 90W charger charge my DEMO-LAPTOP-004 safely?");
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <span>Start Compatibility Verification</span>
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Enter your exact laptop hardware model or choose one of the official hackathon test fixtures.
        </p>

        {/* Quick Test Case Buttons */}
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs font-semibold text-slate-500 self-center mr-1">Quick Fixtures:</span>
          <button
            type="button"
            onClick={() => setOfficialFixture(1)}
            className="text-xs px-3 py-1.5 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 rounded-lg font-medium transition"
          >
            TC1: DDR4 Laptop (RAM-A)
          </button>
          <button
            type="button"
            onClick={() => setOfficialFixture(2)}
            className="text-xs px-3 py-1.5 bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200 rounded-lg font-medium transition"
          >
            TC2: Conflicting Sources (DDR4 vs DDR5)
          </button>
          <button
            type="button"
            onClick={() => setOfficialFixture(3)}
            className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-800 hover:bg-indigo-100 border border-indigo-200 rounded-lg font-medium transition"
          >
            TC3: Ambiguous Model ("Dell laptop")
          </button>
          <button
            type="button"
            onClick={() => setOfficialFixture(4)}
            className="text-xs px-3 py-1.5 bg-orange-50 text-orange-800 hover:bg-orange-100 border border-orange-200 rounded-lg font-medium transition"
          >
            TC4: Universal Claim (Not Trusted)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Natural Language Query Box */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1 flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Natural Language Request (Optional)</span>
            </span>
            <span className="text-[11px] font-normal text-slate-400">Agent extracts intent & model</span>
          </label>
          <input
            type="text"
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            placeholder="e.g. Find a compatible 16 GB DDR4 upgrade for my Lenovo ThinkBook 15 G2"
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm bg-slate-50/50"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Brand */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Device Brand (Optional)
            </label>
            <input
              type="text"
              value={deviceBrand}
              onChange={(e) => setDeviceBrand(e.target.value)}
              placeholder="e.g. Lenovo, Dell, HP, DemoTech"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
            />
          </div>

          {/* Model */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Exact Device Model Number <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={deviceModel}
              onChange={(e) => setDeviceModel(e.target.value)}
              placeholder="e.g. DEMO-LAPTOP-001 or ThinkPad T480"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
            />
          </div>
        </div>

        {/* Part Type Switcher */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
            Component to Check <span className="text-rose-500">*</span>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setPartType("RAM")}
              className={`flex items-center justify-center space-x-2.5 py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                partType === "RAM"
                  ? "bg-sky-50 border-sky-500 text-sky-800 ring-2 ring-sky-200"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Laptop className="w-4 h-4" />
              <span>Laptop RAM Memory</span>
            </button>
            <button
              type="button"
              onClick={() => setPartType("CHARGER")}
              className={`flex items-center justify-center space-x-2.5 py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                partType === "CHARGER"
                  ? "bg-sky-50 border-sky-500 text-sky-800 ring-2 ring-sky-200"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Power Charger / AC Adapter</span>
            </button>
          </div>
        </div>

        {/* Part-Specific Preferences */}
        {partType === "RAM" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
                Requested Upgrade Capacity
              </label>
              <select
                value={requestedCapacity}
                onChange={(e) => setRequestedCapacity(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm bg-white"
              >
                <option value={8}>8 GB Upgrade</option>
                <option value={16}>16 GB Upgrade</option>
                <option value={32}>32 GB Upgrade</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
                Candidate Product SKU (Optional)
              </label>
              <input
                type="text"
                value={candidateSku}
                onChange={(e) => setCandidateSku(e.target.value)}
                placeholder="e.g. RAM-A, RAM-B, RAM-C (auto-picks if empty)"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm bg-white"
              />
            </div>
          </div>
        ) : (
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Candidate Charger SKU (Optional)
            </label>
            <input
              type="text"
              value={candidateSku}
              onChange={(e) => setCandidateSku(e.target.value)}
              placeholder="e.g. UNIVERSAL-CHARGER-001 or CHARGER-OEM-65W-USB-C"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm bg-white"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Leave blank to automatically search for official OEM-compliant chargers in catalogue.
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !deviceModel.trim()}
          className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white font-bold text-sm shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Agent Executing Compatibility Analysis...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Verify Technical Compatibility</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
