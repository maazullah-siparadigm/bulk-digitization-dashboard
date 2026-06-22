import { Panel } from "reactflow"
import { useState } from "react"

export function DocumentStatsPanel({docStats}) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Panel position="top-right">
      <div
        style={{
          background: "white",
          opacity: 0.7,
          borderRadius: 10,
          padding: 12,
          boxShadow: "0 2px 10px rgba(0, 0, 0, 0.16)",
          minWidth: 220,
          fontSize: 14,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: collapsed ? 0 : 10,
            color: "black"
          }}
        >
          <strong>Document Stats</strong>

          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              border: "none",
              background: "transparent",
              cursor: "pointer",
              fontSize: 16,
            }}
          >
            {collapsed ? "▾" : "▴"}
          </button>
        </div>

        {!collapsed && docStats &&  Object.keys(docStats).length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 , color: "#2b2b2bff"}}>
            <div>📄 Total Pages: <b>{docStats.numPages}</b></div>
            <div>📄 Total Tasks: <b>{docStats.totalTasks}</b></div>
            <div>✅ Completed: <b>{docStats.numCompleted}</b></div>
            <div>⏳ Pending: <b>{docStats.numPending}</b></div>
            <div>❌ Failed: <b>{docStats.numFailed}</b></div>
            <div>⚙️ Num. Agentic Calls: <b>{docStats.numAgenticCalls}</b></div>

            <div
              style={{
                marginTop: 6,
                fontSize: 12,
                color: "#6b7280",
              }}
            >
              {/* Last update: {stats.lastUpdated} */}
            </div>
          </div>
        )}
      </div>
    </Panel>
  )
}