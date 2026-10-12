const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });

export const money = (v) => `${v < 0 ? "-" : ""}₹${inr.format(Math.abs(v))}`;

const CURRENCY = new Set([
  "amount", "sender_balance_before", "sender_balance_after", "receiver_balance_before",
  "receiver_balance_after", "sender_avg_amount_so_far", "sender_balance_error", "receiver_balance_delta",
]);
const YES_NO = new Set([
  "receiver_is_merchant", "is_new_receiver", "is_off_hours", "sender_balance_zero",
  "mode_CASH_IN", "mode_CASH_OUT", "mode_DEBIT", "mode_PAYMENT", "mode_TRANSFER",
]);

// Turn a raw feature value into something an analyst can read.
export function formatValue(feature, v) {
  if (CURRENCY.has(feature)) return money(v);
  if (YES_NO.has(feature)) return v ? "Yes" : "No";
  if (feature === "hour_of_day") return `${String(Math.round(v)).padStart(2, "0")}:00`;
  if (feature === "amount_deviation_ratio" || feature === "balance_ratio") return `${v.toFixed(2)}×`;
  return String(Math.round(v * 100) / 100);
}

export const formatTime = (iso) =>
  new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
