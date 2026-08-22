/** Compact money format for market values: €98M, €4.7M, €100K. */
export function formatMoney(value: number): string {
  if (value >= 1_000_000) {
    const millions = value / 1_000_000;
    return `€${millions >= 100 ? Math.round(millions) : millions.toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `€${Math.round(value / 1_000)}K`;
  }
  return `€${Math.round(value)}`;
}
