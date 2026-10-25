import React from "react";
import { ShoppingCart, CheckCircle, Trash2, ArrowRight } from "lucide-react";
import type { CartState } from "../types";

interface CartViewProps {
  cart: CartState | null;
  loading: boolean;
  onRefresh: () => void;
  onClear: () => void;
  onGoToCheck: () => void;
}

export const CartView: React.FC<CartViewProps> = ({
  cart,
  loading,
  onRefresh,
  onClear,
  onGoToCheck
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Mock Store Cart
            </h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center space-x-1">
              <CheckCircle className="w-3 h-3" />
              <span>Independent Store State</span>
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Genuinely hosted on the Mock Shopping Store API. The agent can only add items after explicit approval.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition"
          >
            Refresh Cart
          </button>
          {cart && cart.item_count > 0 && (
            <button
              onClick={onClear}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold border border-rose-200 text-rose-700 hover:bg-rose-50 transition flex items-center space-x-1"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Cart</span>
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">
          Loading remote cart state...
        </div>
      ) : !cart || cart.items.length === 0 ? (
        <div className="py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400 mb-3">
            <ShoppingCart className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-800 text-base">Your Cart is Currently Empty</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-5">
            Run a hardware compatibility analysis on your laptop to identify certified replacement RAM or chargers.
          </p>
          <button
            onClick={onGoToCheck}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow transition inline-flex items-center space-x-2"
          >
            <span>Start Compatibility Check</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          <div className="divide-y divide-slate-100">
            {cart.items.map((item, idx) => (
              <div key={idx} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 text-base">{item.title}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                      SKU: {item.sku}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center space-x-3">
                    <span>Brand: {item.brand}</span>
                    <span>Category: {item.category}</span>
                    <span>Quantity: {item.quantity}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-base font-bold text-slate-900">
                    ${item.total_price.toFixed(2)}
                  </div>
                  <div className="text-xs text-slate-400">
                    ${item.price_per_unit.toFixed(2)} each
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center bg-slate-50 p-4 rounded-xl">
            <div>
              <span className="text-xs font-bold uppercase text-slate-500">Cart Total</span>
              <div className="text-2xl font-black text-slate-900">${cart.subtotal.toFixed(2)}</div>
            </div>
            <div className="text-xs text-slate-500 flex items-center space-x-1.5 mt-2 sm:mt-0">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>Verified genuine state with idempotency audit protection</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
