export function fmtW(w: number | undefined, digits = 0): string {
  if (w === undefined || Number.isNaN(w)) return "—";
  if (w >= 1000) return `${(w / 1000).toFixed(2)} kW`;
  return `${w.toFixed(digits)} W`;
}

export function fmtKwh(kwh: number | undefined, digits = 2): string {
  if (kwh === undefined || Number.isNaN(kwh)) return "—";
  return `${kwh.toFixed(digits)} kWh`;
}

export function fmtMoney(amount: number, currency = "$"): string {
  return `${currency}${amount.toFixed(2)}`;
}

export function fmtTemp(c?: number): string {
  return c === undefined ? "—" : `${c.toFixed(1)} °C`;
}

export function fmtTime(t: number): string {
  return new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function fmtClock(t: number): string {
  return new Date(t).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function fmtRelative(t: number, now: number): string {
  const s = Math.max(0, Math.round((now - t) / 1000));
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m} min ago`;
  return `${Math.round(m / 60)} h ago`;
}
