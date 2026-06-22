export function getStatusColor(status) {
  switch (status) {
    case "COMPLETED":       return "#22c55e";
    case "MARKED_FOR_PROC": return "#4dcebdff";
    case "PROCESSING":      return "#3b82f6";
    case "HANDOFF_PENDING": return "#a844ebff";
    case "FAILED":          return "#ef4444";
    case "PENDING":         return "#9ca3af";
    default:                return "#6b7280";
  }
}
