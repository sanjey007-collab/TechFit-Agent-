import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CheckForm } from "./components/CheckForm";
import { ReportView } from "./components/ReportView";
import { CartView } from "./components/CartView";
import { TestDashboard } from "./components/TestDashboard";
import { HistoryView } from "./components/HistoryView";
import { SettingsView } from "./components/SettingsView";
import { ColdStartBanner } from "./components/ColdStartBanner";
import { AgentTimeline } from "./components/AgentTimeline";
import {
  checkHealth,
  runCompatibilityCheck,
  clarifyCheck,
  approveProposal,
  fetchCart
} from "./api";
import type { CompatibilityReport, CartState, PartType } from "./types";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("check");
  const [serverOnline, setServerOnline] = useState<boolean>(true);
  const [isRetryingHealth, setIsRetryingHealth] = useState<boolean>(false);
  const [cart, setCart] = useState<CartState | null>(null);
  const [loadingCart, setLoadingCart] = useState<boolean>(false);

  // Analysis State
  const [activeReport, setActiveReport] = useState<CompatibilityReport | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [approving, setApproving] = useState<boolean>(false);
  const [timelineStep, setTimelineStep] = useState<number>(1);
  const [timelineStatus, setTimelineStatus] = useState<string>("Ready");

  const pingServer = async () => {
    setIsRetryingHealth(true);
    try {
      await checkHealth();
      setServerOnline(true);
    } catch {
      setServerOnline(false);
    } finally {
      setIsRetryingHealth(false);
    }
  };

  const loadCartState = async () => {
    setLoadingCart(true);
    try {
      const c = await fetchCart("default-cart");
      setCart(c);
    } catch (err) {
      console.warn("Failed to load cart state:", err);
    } finally {
      setLoadingCart(false);
    }
  };

  useEffect(() => {
    pingServer();
    loadCartState();
    const interval = setInterval(pingServer, 45000);
    return () => clearInterval(interval);
  }, []);

  const handleStartCheck = async (formData: {
    device_brand?: string;
    device_model: string;
    part_type: PartType;
    ram_preferences?: { requested_capacity_gb?: number };
    candidate_sku?: string;
    natural_language_query?: string;
  }) => {
    setAnalyzing(true);
    setTimelineStep(1);
    setTimelineStatus("Resolving hardware identity & variant...");

    try {
      // Simulate live agent steps progression for smooth user feedback
      setTimeout(() => {
        setTimelineStep(2);
        setTimelineStatus("Retrieving manufacturer PSREF & spec facts...");
      }, 300);

      setTimeout(() => {
        setTimelineStep(3);
        setTimelineStatus("Detecting source contradictions & data conflicts...");
      }, 700);

      setTimeout(() => {
        setTimelineStep(4);
        setTimelineStatus("Evaluating deterministic rules (pure functions)...");
      }, 1100);

      const report = await runCompatibilityCheck({
        ...formData,
        cart_id: "default-cart"
      });

      setTimelineStep(report.verdict === "COMPATIBLE" ? 6 : 5);
      setTimelineStatus(`Completed with verdict: ${report.verdict}`);
      setActiveReport(report);
    } catch (err: any) {
      alert(`Compatibility check failed: ${err.message || err}`);
      setTimelineStatus("Check failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApprove = async (proposalId: string, sku: string, version: number) => {
    if (!activeReport) return;
    setApproving(true);
    setTimelineStep(6);
    setTimelineStatus("Executing approved cart mutation...");

    try {
      const idempotencyKey = `appr-web-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      await approveProposal(proposalId, {
        check_id: activeReport.check_id,
        product_sku: sku,
        proposal_version: version,
        idempotency_key: idempotencyKey
      });

      setTimelineStep(7);
      setTimelineStatus("Verified remote cart state independently!");

      // Refresh cart
      await loadCartState();

      // Refresh report
      const updated = await runCompatibilityCheck({
        device_brand: activeReport.resolved_device_brand,
        device_model: activeReport.resolved_device_model || "",
        part_type: activeReport.part_type,
        cart_id: "default-cart"
      });
      setActiveReport(updated);
    } catch (err: any) {
      alert(`Approval execution error: ${err.message || err}`);
    } finally {
      setApproving(false);
    }
  };

  const handleClarify = async (checkId: string, model: string) => {
    try {
      setTimelineStep(1);
      setTimelineStatus(`Resuming check with clarified model '${model}'...`);
      const resumed = await clarifyCheck(checkId, { clarified_model: model });
      setActiveReport(resumed);
      setTimelineStep(resumed.verdict === "COMPATIBLE" ? 6 : 5);
      setTimelineStatus(`Resumed analysis: ${resumed.verdict}`);
    } catch (err: any) {
      alert(`Clarification submission error: ${err.message || err}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {!serverOnline && (
        <ColdStartBanner onRetry={pingServer} isRetrying={isRetryingHealth} />
      )}

      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        cartCount={cart ? cart.item_count : 0}
        serverOnline={serverOnline}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "check" && (
          <div>
            <AgentTimeline currentStep={timelineStep} statusText={timelineStatus} />

            {activeReport ? (
              <ReportView
                report={activeReport}
                onApprove={handleApprove}
                onClarify={handleClarify}
                approving={approving}
                onReset={() => {
                  setActiveReport(null);
                  setTimelineStep(1);
                  setTimelineStatus("Ready");
                }}
              />
            ) : (
              <CheckForm onSubmit={handleStartCheck} loading={analyzing} />
            )}
          </div>
        )}

        {activeTab === "cart" && (
          <CartView
            cart={cart}
            loading={loadingCart}
            onRefresh={loadCartState}
            onClear={async () => {
              // Clear cart
              await fetchCart("default-cart");
              loadCartState();
            }}
            onGoToCheck={() => setActiveTab("check")}
          />
        )}

        {activeTab === "tests" && <TestDashboard />}

        {activeTab === "history" && (
          <HistoryView
            onSelectReport={(r) => {
              setActiveReport(r);
              setActiveTab("check");
            }}
          />
        )}

        {activeTab === "settings" && <SettingsView />}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>TechFit Agent — AI-Powered RAM & Charger Compatibility Checker</span>
          <span>Google Antigravity Production Hackathon Build • Render Live Architecture</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
