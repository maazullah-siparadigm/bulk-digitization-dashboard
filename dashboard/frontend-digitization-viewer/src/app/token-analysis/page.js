"use client"
import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp, RefreshCw, Clock } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import { getTokenAggregates, getTokenHistograms, getTokenAggregatesByAgentModel } from "@/api/documents";

const STORAGE_KEY = "token_analysis_data";

// Price per 1M tokens (USD). Populate with real values when known.
const MODEL_PRICING = {
  "gemini-3.5-flash" : {input: 0.75, output: 4.5, thinking: 4.5},
  "gemini-2.5-flash": {input: 0.15, output: 1.25, thinking: 1.25},
  "gemini-2.5-flash-lite": {input: 0.05, output: 0.20, thinking: 0.20},
  "gemini-3-flash-preview" : {input: 0.25 , output: 1.50, thinking: 1.50},
};

function calculateCost(model, inputTokens, outputTokens, thinkingTokens) {
  const p = MODEL_PRICING[model] ?? { input: 0, output: 0, thinking: 0 };
  return {
    input:    (inputTokens    / 1_000_000) * p.input,
    output:   (outputTokens   / 1_000_000) * p.output,
    thinking: (thinkingTokens / 1_000_000) * p.thinking,
    total:    (inputTokens    / 1_000_000) * p.input +
              (outputTokens   / 1_000_000) * p.output +
              (thinkingTokens / 1_000_000) * p.thinking,
  };
}

const TOKEN_TYPES = [
  { key: "input_tokens",    label: "Input Tokens",    color: "#3b82f6" },
  { key: "output_tokens",   label: "Output Tokens",   color: "#22c55e" },
  { key: "thinking_tokens", label: "Thinking Tokens", color: "#a844eb" },
];

function formatTokenCount(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatTimestamp(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1)  return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24)  return `${diffHrs}h ago`;
  return d.toLocaleDateString();
}

function computeHistogramStats(data) {
  if (!data || data.length === 0) return null;
  const total = data.reduce((s, b) => s + b.count, 0);
  if (total === 0) return null;

  const midpoints = data.map(b => (b.bin_start + b.bin_end) / 2);
  const mean = midpoints.reduce((s, m, i) => s + m * data[i].count, 0) / total;

  let cumulative = 0;
  let median = midpoints[0];
  for (let i = 0; i < data.length; i++) {
    cumulative += data[i].count;
    if (cumulative >= total / 2) { median = midpoints[i]; break; }
  }

  const modeIdx = data.reduce((best, b, i) => b.count > data[best].count ? i : best, 0);
  const mode = midpoints[modeIdx];

  const variance = midpoints.reduce((s, m, i) => s + data[i].count * Math.pow(m - mean, 2), 0) / total;
  const stdDev = Math.sqrt(variance);

  return { mean, median, mode, stdDev, total };
}

function HistogramStatStrip({ data }) {
  const stats = computeHistogramStats(data);
  if (!stats) return null;
  const items = [
    { label: "n",      value: stats.total.toLocaleString() },
    { label: "mean",   value: formatTokenCount(Math.round(stats.mean)) },
    { label: "median", value: formatTokenCount(Math.round(stats.median)) },
    { label: "mode",   value: formatTokenCount(Math.round(stats.mode)) },
    { label: "σ",      value: formatTokenCount(Math.round(stats.stdDev)) },
  ];
  return (
    <div className="flex justify-center gap-3 flex-wrap mt-1">
      {items.map(({ label, value }) => (
        <div key={label} className="flex gap-1 text-xs">
          <span className="text-gray-500">{label}</span>
          <span className="text-gray-300 font-mono">{value}</span>
        </div>
      ))}
    </div>
  );
}

function HistogramChart({ title, data, color }) {
  const formatted = (data ?? []).map(b => ({
    bin: formatTokenCount(b.bin_start),
    label: `${formatTokenCount(b.bin_start)}–${formatTokenCount(b.bin_end)}`,
    count: b.count,
  }));

  return (
    <div className="flex flex-col gap-1 flex-1 min-w-0">
      <p className="text-xs font-semibold text-center" style={{ color }}>{title}</p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={formatted} margin={{ top: 4, right: 8, left: 0, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="bin"
            tick={{ fill: "#9ca3af", fontSize: 9 }}
            interval="preserveStartEnd"
            minTickGap={40}
          />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 9 }} width={32} />
          <Tooltip
            labelFormatter={(_, payload) => payload?.[0]?.payload?.label ?? ""}
            contentStyle={{ backgroundColor: "#1f2937", border: "none", fontSize: 11 }}
            labelStyle={{ color: "#e5e7eb" }}
            itemStyle={{ color }}
          />
          <Bar dataKey="count" fill={color} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <HistogramStatStrip data={data} />
    </div>
  );
}

function GroupHistogramRow({ groupName, groupData }) {
  return (
    <div className="flex flex-col gap-2 bg-gray-700 rounded-lg p-3">
      <p className="text-sm font-semibold text-gray-200">{groupName}</p>
      <div className="flex gap-4">
        {TOKEN_TYPES.map(t => (
          <HistogramChart
            key={t.key}
            title={t.label}
            data={groupData?.[t.key]}
            color={t.color}
          />
        ))}
      </div>
    </div>
  );
}

function GroupByToggle({ value, onChange }) {
  return (
    <div className="flex gap-2">
      {["model", "agent"].map(opt => (
        <button
          key={opt}
          onClick={e => { e.stopPropagation(); onChange(opt); }}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
            value === opt ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          By {opt.charAt(0).toUpperCase() + opt.slice(1)}
        </button>
      ))}
    </div>
  );
}

export default function TokenAnalysis() {
  const [data, setData] = useState(null);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState(null);
  const [totalsOpen, setTotalsOpen] = useState(true);
  const [histogramsOpen, setHistogramsOpen] = useState(true);
  const [histogramsGroupBy, setHistogramsGroupBy] = useState("model");
  const [pricingOpen, setPricingOpen] = useState(true);
  const [pricingGroupBy, setPricingGroupBy] = useState("model");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setData(JSON.parse(stored));
    } catch {
      /* ignore corrupt storage */
    }
  }, []);

  async function fetchAll() {
    setIsFetching(true);
    setError(null);
    try {
      const [aggregatesModel, aggregatesAgent, histogramsModel, histogramsAgent, agentModelBreakdown] = await Promise.all([
        getTokenAggregates("model"),
        getTokenAggregates("agent"),
        getTokenHistograms("model"),
        getTokenHistograms("agent"),
        getTokenAggregatesByAgentModel(),
      ]);
      const next = {
        aggregates: { model: aggregatesModel, agent: aggregatesAgent },
        histograms: { model: histogramsModel, agent: histogramsAgent },
        agentModelBreakdown,
        fetchedAt: new Date().toISOString(),
      };
      setData(next);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (err) {
      setError("Failed to fetch token data. Check the backend.");
      console.error(err);
    } finally {
      setIsFetching(false);
    }
  }

  const aggregatesBarData = data?.aggregates?.model
    ? Object.entries(data.aggregates.model).map(([name, tokens]) => ({ name, ...tokens }))
    : [];

  const histogramGroups = data?.histograms?.[histogramsGroupBy]
    ? Object.entries(data.histograms[histogramsGroupBy])
    : [];

  const pricingRows = data?.aggregates?.model
    ? Object.entries(data.aggregates.model).map(([model, tokens]) => {
        const cost = calculateCost(
          model,
          tokens.input_tokens ?? 0,
          tokens.output_tokens ?? 0,
          tokens.thinking_tokens ?? 0,
        );
        return { model, ...tokens, cost };
      })
    : [];

  // Per-agent cost: sum costs across all models each agent used
  const agentPricingRows = data?.agentModelBreakdown
    ? Object.entries(data.agentModelBreakdown).map(([agent, modelMap]) => {
        let input_tokens = 0, output_tokens = 0, thinking_tokens = 0;
        let cost_input = 0, cost_output = 0, cost_thinking = 0;
        Object.entries(modelMap).forEach(([model, tokens]) => {
          const t_in  = tokens.input_tokens    ?? 0;
          const t_out = tokens.output_tokens   ?? 0;
          const t_th  = tokens.thinking_tokens ?? 0;
          input_tokens    += t_in;
          output_tokens   += t_out;
          thinking_tokens += t_th;
          const c = calculateCost(model, t_in, t_out, t_th);
          cost_input    += c.input;
          cost_output   += c.output;
          cost_thinking += c.thinking;
        });
        return { agent, input_tokens, output_tokens, thinking_tokens, cost_input, cost_output, cost_thinking, cost_total: cost_input + cost_output + cost_thinking };
      })
    : [];

  const agentPricingTotals = agentPricingRows.reduce(
    (acc, r) => ({
      input_tokens:    acc.input_tokens    + r.input_tokens,
      output_tokens:   acc.output_tokens   + r.output_tokens,
      thinking_tokens: acc.thinking_tokens + r.thinking_tokens,
      cost_input:    acc.cost_input    + r.cost_input,
      cost_output:   acc.cost_output   + r.cost_output,
      cost_thinking: acc.cost_thinking + r.cost_thinking,
      cost_total:    acc.cost_total    + r.cost_total,
    }),
    { input_tokens: 0, output_tokens: 0, thinking_tokens: 0, cost_input: 0, cost_output: 0, cost_thinking: 0, cost_total: 0 },
  );

  const pricingTotals = pricingRows.reduce(
    (acc, r) => ({
      input_tokens:    acc.input_tokens    + (r.input_tokens    ?? 0),
      output_tokens:   acc.output_tokens   + (r.output_tokens   ?? 0),
      thinking_tokens: acc.thinking_tokens + (r.thinking_tokens ?? 0),
      cost_input:    acc.cost_input    + (r.cost?.input    ?? 0),
      cost_output:   acc.cost_output   + (r.cost?.output   ?? 0),
      cost_thinking: acc.cost_thinking + (r.cost?.thinking ?? 0),
      cost_total:    acc.cost_total    + (r.cost?.total    ?? 0),
    }),
    { input_tokens: 0, output_tokens: 0, thinking_tokens: 0, cost_input: 0, cost_output: 0, cost_thinking: 0, cost_total: 0 },
  );

  return (
    <div className="flex flex-col h-full w-full bg-gray-800 rounded-lg p-5 gap-3 overflow-y-auto">

      {/* Header */}
      <div className="flex items-center justify-between px-10 py-2">
        <h1 className="text-lg font-bold text-white">Token Analysis</h1>
        <div className="flex items-center gap-4">
          {data?.fetchedAt && (
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Clock size={12} />
              <span>Last fetched: {formatTimestamp(data.fetchedAt)}</span>
            </div>
          )}
          <button
            onClick={fetchAll}
            disabled={isFetching}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium text-white transition"
          >
            <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
            {isFetching ? "Fetching…" : "Fetch Token Counts"}
          </button>
        </div>
      </div>

      {error && (
        <p className="mx-10 px-3 py-2 rounded bg-red-900 text-red-300 text-sm">{error}</p>
      )}

      {!data && !isFetching && (
        <p className="mx-10 text-gray-400 text-sm">
          No data yet. Click <span className="text-white font-medium">Fetch Token Counts</span> to load.
        </p>
      )}

      {/* Token Totals */}
      {data && (
        <div className="px-10 py-2 flex flex-col gap-1">
          <div
            className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
            onClick={() => setTotalsOpen(o => !o)}
          >
            <h2 className="text-sm font-semibold text-gray-200">Token Totals</h2>
            {totalsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>

          {totalsOpen && (
            <div className="bg-gray-700 rounded-lg p-4">
              {aggregatesBarData.length === 0 ? (
                <p className="text-gray-400 text-sm">No aggregate data.</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={aggregatesBarData} margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                    <YAxis tickFormatter={formatTokenCount} tick={{ fill: "#9ca3af", fontSize: 11 }} />
                    <Tooltip
                      formatter={(v, name) => [formatTokenCount(v), name.replace(/_/g, " ")]}
                      contentStyle={{ backgroundColor: "#1f2937", border: "none", fontSize: 12 }}
                      labelStyle={{ color: "#e5e7eb" }}
                    />
                    <Legend formatter={name => name.replace(/_/g, " ")} wrapperStyle={{ color: "#9ca3af", fontSize: 12 }} />
                    {TOKEN_TYPES.map(t => (
                      <Bar key={t.key} dataKey={t.key} name={t.key} fill={t.color} radius={[3, 3, 0, 0]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          )}
        </div>
      )}

      {/* Token Distribution Histograms */}
      {data && (
        <div className="px-10 py-2 flex flex-col gap-1">
          <div
            className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
            onClick={() => setHistogramsOpen(o => !o)}
          >
            <h2 className="text-sm font-semibold text-gray-200">Token Distribution</h2>
            <div className="flex items-center gap-2">
              <GroupByToggle value={histogramsGroupBy} onChange={setHistogramsGroupBy} />
              {histogramsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
          </div>

          {histogramsOpen && (
            <div className="flex flex-col gap-3">
              {histogramGroups.length === 0 ? (
                <p className="text-gray-400 text-sm">No histogram data.</p>
              ) : (
                histogramGroups.map(([groupName, groupData]) => (
                  <GroupHistogramRow
                    key={groupName}
                    groupName={groupName}
                    groupData={groupData}
                  />
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Token Pricing */}
      {data && (
        <div className="px-10 py-2 flex flex-col gap-1">
          <div
            className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
            onClick={() => setPricingOpen(o => !o)}
          >
            <h2 className="text-sm font-semibold text-gray-200">Token Pricing</h2>
            <div className="flex items-center gap-2">
              <GroupByToggle value={pricingGroupBy} onChange={setPricingGroupBy} />
              {pricingOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
          </div>

          {pricingOpen && (
            <div className="bg-gray-700 rounded-lg overflow-x-auto">
              {pricingGroupBy === "model" ? (
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold whitespace-nowrap">Model</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[0].color }}>Input Tokens</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[1].color }}>Output Tokens</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[2].color }}>Thinking Tokens</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Input Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Output Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Thinking Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-400 font-semibold whitespace-nowrap">Total Cost ($)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pricingRows.map((row, i) => (
                      <tr key={row.model} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                        <td className="p-2 font-semibold text-gray-200 whitespace-nowrap">{row.model}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{(row.input_tokens ?? 0).toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{(row.output_tokens ?? 0).toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{(row.thinking_tokens ?? 0).toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost.input.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost.output.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost.thinking.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-300 font-bold">${row.cost.total.toFixed(4)}</td>
                      </tr>
                    ))}
                    <tr className="bg-gray-900 border-t border-gray-600">
                      <td className="p-2 font-bold text-gray-100">TOTAL</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{pricingTotals.input_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{pricingTotals.output_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{pricingTotals.thinking_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${pricingTotals.cost_input.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${pricingTotals.cost_output.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${pricingTotals.cost_thinking.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-400">${pricingTotals.cost_total.toFixed(4)}</td>
                    </tr>
                  </tbody>
                </table>
              ) : agentPricingRows.length === 0 ? (
                <p className="p-3 text-gray-400 text-sm">No agent breakdown data. Fetch token counts to load.</p>
              ) : (
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold whitespace-nowrap">Agent</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[0].color }}>Input Tokens</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[1].color }}>Output Tokens</th>
                      <th className="text-right p-2 bg-gray-900 font-semibold whitespace-nowrap" style={{ color: TOKEN_TYPES[2].color }}>Thinking Tokens</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Input Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Output Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-300 font-semibold whitespace-nowrap">Thinking Cost ($)</th>
                      <th className="text-right p-2 bg-gray-900 text-yellow-400 font-semibold whitespace-nowrap">Total Cost ($)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentPricingRows.map((row, i) => (
                      <tr key={row.agent} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                        <td className="p-2 font-semibold text-gray-200 whitespace-nowrap">{row.agent}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{row.input_tokens.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{row.output_tokens.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-gray-300">{row.thinking_tokens.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost_input.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost_output.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-200">${row.cost_thinking.toFixed(4)}</td>
                        <td className="p-2 text-right font-mono text-yellow-300 font-bold">${row.cost_total.toFixed(4)}</td>
                      </tr>
                    ))}
                    <tr className="bg-gray-900 border-t border-gray-600">
                      <td className="p-2 font-bold text-gray-100">TOTAL</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{agentPricingTotals.input_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{agentPricingTotals.output_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-white">{agentPricingTotals.thinking_tokens.toLocaleString()}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${agentPricingTotals.cost_input.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${agentPricingTotals.cost_output.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-300">${agentPricingTotals.cost_thinking.toFixed(4)}</td>
                      <td className="p-2 text-right font-mono font-bold text-yellow-400">${agentPricingTotals.cost_total.toFixed(4)}</td>
                    </tr>
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
