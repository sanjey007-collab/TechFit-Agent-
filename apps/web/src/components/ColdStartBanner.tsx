import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ColdStartBannerProps {
  onRetry: () => void;
  isRetrying: boolean;
}

export const ColdStartBanner: React.FC<ColdStartBannerProps> = ({ onRetry, isRetrying }) => {
  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-amber-900 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>Waking up backend services...</strong> On Render free instances, services spin down after inactivity. Cold starts can take ~30-45 seconds.
          </span>
        </div>
        <button
          onClick={onRetry}
          disabled={isRetrying}
          className="px-3 py-1 bg-amber-200/70 hover:bg-amber-200 text-amber-900 rounded-lg font-semibold flex items-center space-x-1 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isRetrying ? "animate-spin" : ""}`} />
          <span>Retry Connection</span>
        </button>
      </div>
    </div>
  );
};
