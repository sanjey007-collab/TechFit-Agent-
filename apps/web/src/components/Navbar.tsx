import React from "react";
import { Cpu, ShoppingCart, CheckCircle, ShieldCheck, History, Settings as SettingsIcon } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  cartCount: number;
  serverOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  cartCount,
  serverOnline
}) => {
  const tabs = [
    { id: "check", label: "Check Compatibility", icon: Cpu },
    { id: "cart", label: "Mock Cart", icon: ShoppingCart, count: cartCount },
    { id: "tests", label: "Test Dashboard", icon: ShieldCheck },
    { id: "history", label: "Audit History", icon: History },
    { id: "settings", label: "API & System", icon: SettingsIcon }
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("check")}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">TechFit Agent</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200">
                  AI + Deterministic Rules
                </span>
              </div>
              <p className="text-xs text-slate-500">Exact RAM & Charger Hardware Compatibility</p>
            </div>
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-slate-900 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                  {tab.count !== undefined && tab.count > 0 && (
                    <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                      isActive ? "bg-white text-slate-900" : "bg-sky-600 text-white"
                    }`}>
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}

            <div className="ml-3 pl-3 border-l border-slate-200 flex items-center space-x-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${serverOnline ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
              <span className="text-xs text-slate-500 hidden sm:inline">
                {serverOnline ? "API Live" : "Connecting..."}
              </span>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};
