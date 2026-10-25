import React, { useEffect, useState } from "react";
import { Settings, CheckCircle2, XCircle, Key, Server, Database, Shield } from "lucide-react";
import type { ConfigStatusResponse } from "../types";
import { fetchConfigStatus } from "../api";

export const SettingsView: React.FC = () => {
  const [config, setConfig] = useState<ConfigStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfigStatus()
      .then((data) => setConfig(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-slate-200">
          <div className="p-2 bg-slate-100 text-slate-700 rounded-lg">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Configuration & API Keys Status</h2>
            <p className="text-xs text-slate-500">Live inspection of runtime credentials, databases, and Render services status.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Inspecting system status...</div>
        ) : !config ? (
          <div className="p-4 bg-amber-50 text-amber-800 rounded-xl border border-amber-200 text-xs">
            Unable to connect to configuration status endpoint. Ensure the backend API is online.
          </div>
        ) : (
          <div className="space-y-6">
            {/* 3 Required API Keys Status */}
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
                <Key className="w-4 h-4 text-sky-600" />
                <span>Onboarded API Keys (Server-Side Masked)</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. Gemini */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-slate-900 text-sm">Key #1: Google Gemini</span>
                    {config.keys.gemini.configured ? (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>CONFIGURED</span>
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <XCircle className="w-3 h-3" />
                        <span>MISSING</span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600 space-y-1 font-mono">
                    <div>Model: {config.keys.gemini.model}</div>
                    <div>Key: {config.keys.gemini.masked || "Not provided"}</div>
                  </div>
                </div>

                {/* 2. Search Provider */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-slate-900 text-sm">Key #2: Search Provider</span>
                    {config.keys.search.configured ? (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>CONFIGURED</span>
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <XCircle className="w-3 h-3" />
                        <span>MISSING</span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600 space-y-1 font-mono">
                    <div>Provider: {config.keys.search.provider}</div>
                    <div>Key: {config.keys.search.masked || "Not provided"}</div>
                  </div>
                </div>

                {/* 3. Product Details */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-slate-900 text-sm">Key #3: Product Details</span>
                    {config.keys.product_details.configured ? (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>CONFIGURED</span>
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full flex items-center space-x-1">
                        <span>FALLBACK</span>
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600 space-y-1 font-mono">
                    <div>Provider: {config.keys.product_details.provider}</div>
                    <div>Key: {config.keys.product_details.masked || "Mock Store Fallback"}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Infrastructure & Services */}
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
                <Server className="w-4 h-4 text-indigo-600" />
                <span>Backend Services & Database</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center space-x-3">
                  <Database className="w-6 h-6 text-indigo-600" />
                  <div>
                    <span className="font-bold text-slate-900 text-sm">Database Engine</span>
                    <p className="text-xs text-slate-500 font-mono">
                      {config.services.database.engine.toUpperCase()} (Transactional async session pool)
                    </p>
                  </div>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center space-x-3">
                  <Shield className="w-6 h-6 text-emerald-600" />
                  <div>
                    <span className="font-bold text-slate-900 text-sm">Mock Store Service</span>
                    <p className="text-xs text-slate-500 font-mono">
                      Token authenticated ({config.services.mock_store.url})
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Render Blueprint Info */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-slate-600 space-y-2">
              <span className="font-bold text-slate-800 text-sm block">Render Live Blueprint Deployment</span>
              <p>
                This monorepo includes a committed <code className="bg-white px-1.5 py-0.5 border rounded">render.yaml</code> Blueprint declaring all four services: Frontend Static Site, Backend API Web Service, Mock Store Web Service, and Managed PostgreSQL Database.
              </p>
              <p className="text-slate-500 italic">
                Render free-tier instances sleep after 15 minutes of inactivity. When accessed cold, services may take 30-50 seconds to spin up.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
