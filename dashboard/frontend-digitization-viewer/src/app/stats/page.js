"use client"
import { ChevronDown, ChevronUp, RefreshCw } from "lucide-react";
import { useState, useEffect } from "react";
import Metric from "@/components/Metric";
import { getDocumentCounts, getTaskStatusCounts, getBatchCountsByModel, getRequestsCountPerBatch, getFailedTasksByDocument, getCompletedPagesOverTime, getStageModels } from "@/api/documents";
import { getStatusColor } from "@/utils/statusColors";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

const STATUS_COLUMNS = [
    "PENDING",
    "MARKED_FOR_PROC",
    "SUBMITTED",
    "STARTED",
    "PROCESSING",
    "HANDOFF_PENDING",
    "COMPLETED",
    "FAILED",
];

const BATCH_STATUS_COLUMNS = [
    "PENDING",
    "SUBMITTED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
];

const BATCH_STATUS_ORDER = {
    "SUBMITTED":  0,
    "PENDING":    1,
    "COMPLETED":  2,
    "FAILED":     3,
    "CANCELLED":  4,
    "EXPIRED":    5,
};

const BATCH_STATUS_COLORS = {
    "PENDING":   "#9ca3af",
    "SUBMITTED": "#3b82f6",
    "COMPLETED": "#22c55e",
    "FAILED":    "#ef4444",
    "CANCELLED": "#6b7280",
    "EXPIRED":   "#f59e0b",
};

export default function Stats() {
    const [metricsDropdownOpen, setMetricsDropDownOpen] = useState(true);
    const [stagesDropdownOpen, setStagesDropdownOpen] = useState(true);
    const [modelStatusDropdownOpen, setModelStatusDropdownOpen] = useState(true);
    const [batchDropdownOpen, setBatchDropdownOpen] = useState(true);
    const [requestsDropdownOpen, setRequestsDropdownOpen] = useState(true);
    const [failedTasksDropdownOpen, setFailedTasksDropdownOpen] = useState(true);
    const [docMetrics, setDocMetrics] = useState({
        "total-docs":      { title: "Total Documents",    value: null },
        "total-digitized": { title: "Total Digitized",    value: null },
        "total-failed":    { title: "Digitization Failed", value: null },
    });
    const [pageMetrics, setPageMetrics] = useState({
        "total-pages":          { title: "Total Pages",         value: null },
        "pages-digitized":      { title: "Total Digitized",     value: null },
        "pages-failed":         { title: "Digitization Failed", value: null },
    });
    const [taskStatusCounts, setTaskStatusCounts] = useState(null);
    // Stage name → configured model, served by the backend from the stage configs.
    // Stages missing from it (compute stages) are grouped under "other".
    const [stageModels, setStageModels] = useState({});
    const [batchCountsByModel, setBatchCountsByModel] = useState(null);
    const [requestsCountPerBatch, setRequestsCountPerBatch] = useState(null);
    const [failedTasksByDocument, setFailedTasksByDocument] = useState(null);
    const [completionWindow, setCompletionWindow] = useState(7);
    const [completionGranularity, setCompletionGranularity] = useState("day");
    const [completionData, setCompletionData] = useState(null);
    const [completionFetchedAt, setCompletionFetchedAt] = useState(null);
    const [completionSyncing, setCompletionSyncing] = useState(false);

    const WINDOW_OPTIONS = [1, 2, 3, 5, 7];

    useEffect(() => {
        async function fetchStats() {
            try {
                const counts = await getDocumentCounts();
                const pct = (num, denom) =>
                    denom > 0 ? `${((num / denom) * 100).toFixed(1)}% of total` : null;
                setDocMetrics({
                    "total-docs":      { title: "Total Documents",     value: counts.total?.toLocaleString() },
                    "total-digitized": { title: "Total Digitized",     value: counts.completed?.toLocaleString(),           subtitle: pct(counts.completed, counts.total) },
                    "total-failed":    { title: "Digitization Failed", value: counts.digitization_failed?.toLocaleString(), subtitle: pct(counts.digitization_failed, counts.total) },
                });
                setPageMetrics({
                    "total-pages":     { title: "Total Pages",         value: counts.total_pages?.toLocaleString() },
                    "pages-digitized": { title: "Total Digitized",     value: counts.completed_pages?.toLocaleString(),  subtitle: pct(counts.completed_pages, counts.total_pages) },
                    "pages-failed":    { title: "Digitization Failed", value: counts.failed_pages?.toLocaleString(),     subtitle: pct(counts.failed_pages, counts.total_pages) },
                });
            } catch (err) {
                console.error("Failed to fetch stats:", err);
            }
        }

        async function fetchTaskStatusCounts() {
            try {
                const counts = await getTaskStatusCounts();
                setTaskStatusCounts(counts);
            } catch (err) {
                console.error("Failed to fetch task status counts:", err);
            }
        }

        async function fetchStageModels() {
            try {
                const data = await getStageModels();
                setStageModels(data?.error ? {} : data);
            } catch (err) {
                console.error("Failed to fetch stage models:", err);
            }
        }

        async function fetchBatchCountsByModel() {
            try {
                const counts = await getBatchCountsByModel();
                setBatchCountsByModel(counts);
            } catch (err) {
                console.error("Failed to fetch batch counts by model:", err);
            }
        }

        async function fetchRequestsCountPerBatch() {
            try {
                const data = await getRequestsCountPerBatch();
                setRequestsCountPerBatch(data);
            } catch (err) {
                console.error("Failed to fetch requests count per batch:", err);
            }
        }

        async function fetchFailedTasksByDocument() {
            try {
                const data = await getFailedTasksByDocument();
                setFailedTasksByDocument(data);
            } catch (err) {
                console.error("Failed to fetch failed tasks by document:", err);
            }
        }

        fetchStats();
        fetchStageModels();
        fetchTaskStatusCounts();
        fetchBatchCountsByModel();
        fetchRequestsCountPerBatch();
        fetchFailedTasksByDocument();
        const interval = setInterval(() => {
            fetchStats();
            fetchTaskStatusCounts();
            fetchBatchCountsByModel();
            fetchRequestsCountPerBatch();
            fetchFailedTasksByDocument();
        }, 15000);
        return () => clearInterval(interval);
    }, []);

    const COMPLETION_CACHE_KEY = "completion_pages_cache";

    function getCompletionCacheEntry(window, granularity) {
        try {
            const raw = localStorage.getItem(COMPLETION_CACHE_KEY);
            if (!raw) return null;
            return JSON.parse(raw)[`${window}_${granularity}`] ?? null;
        } catch { return null; }
    }

    function setCompletionCacheEntry(window, granularity, data) {
        try {
            const raw = localStorage.getItem(COMPLETION_CACHE_KEY);
            const cache = raw ? JSON.parse(raw) : {};
            const entry = { data, fetchedAt: new Date().toISOString() };
            cache[`${window}_${granularity}`] = entry;
            localStorage.setItem(COMPLETION_CACHE_KEY, JSON.stringify(cache));
            return entry;
        } catch { return null; }
    }

    useEffect(() => {
        const entry = getCompletionCacheEntry(completionWindow, completionGranularity);
        if (entry) {
            setCompletionData(entry.data);
            setCompletionFetchedAt(entry.fetchedAt);
        } else {
            setCompletionData(null);
            setCompletionFetchedAt(null);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [completionWindow, completionGranularity]);

    async function syncCompletionData() {
        setCompletionSyncing(true);
        try {
            const data = await getCompletedPagesOverTime(completionWindow, completionGranularity);
            const entry = setCompletionCacheEntry(completionWindow, completionGranularity, data);
            setCompletionData(data);
            setCompletionFetchedAt(entry?.fetchedAt ?? new Date().toISOString());
        } catch (err) {
            console.error("Failed to fetch completion data:", err);
        } finally {
            setCompletionSyncing(false);
        }
    }

    function formatCompletionTick(timestamp, granularity) {
        const d = new Date(timestamp);
        if (granularity === "hour") {
            return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:00`;
        }
        return d.toLocaleDateString("default", { month: "short", day: "numeric" });
    }

    const stages = taskStatusCounts ? Object.keys(taskStatusCounts) : [];
    const models = batchCountsByModel ? Object.keys(batchCountsByModel) : [];

    const modelStatusCounts = (() => {
        if (!taskStatusCounts) return null;
        const result = {};
        Object.entries(taskStatusCounts).forEach(([stage, counts]) => {
            const model = stageModels[stage] ?? "other";
            if (!result[model]) result[model] = {};
            STATUS_COLUMNS.forEach(status => {
                result[model][status] = (result[model][status] ?? 0) + (counts[status] ?? 0);
            });
        });
        return result;
    })();

    return (
        <div className="flex flex-col h-full w-full bg-gray-800 rounded-lg p-5 gap-3 overflow-y-auto">
            <div className="px-10 py-2 flex flex-col gap-1" onClick={() => setMetricsDropDownOpen(!metricsDropdownOpen)}>
                <div className="flex justify-between items-center p-2 bg-gray-900 rounded-lg">
                    <h2>Metrics</h2>
                    {metricsDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {metricsDropdownOpen && (
                <div className="flex flex-col gap-2">
                    <div className="flex-1 flex w-full gap-3">
                        {Object.entries(docMetrics).map(([key, metric]) => (
                        <div key={key} className="flex flex-col w-full bg-gray-700 rounded-lg">
                            <Metric title={metric.title} value={metric.value} subtitle={metric.subtitle} />
                        </div>
                        ))}
                    </div>
                    <div className="flex-1 flex w-full gap-3">
                        {Object.entries(pageMetrics).map(([key, metric]) => (
                        <div key={key} className="flex flex-col w-full bg-gray-700 rounded-lg">
                            <Metric title={metric.title} value={metric.value} subtitle={metric.subtitle} />
                        </div>
                        ))}
                    </div>

                    {/* Pages Completed Over Time */}
                    <div className="bg-gray-700 rounded-lg p-4 flex flex-col gap-3" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <div className="flex flex-col gap-0.5">
                                <p className="text-sm font-semibold text-gray-200">Pages Completed</p>
                                {completionFetchedAt ? (
                                    <p className="text-xs text-gray-500">
                                        Last synced: {new Date(completionFetchedAt).toLocaleString()}
                                    </p>
                                ) : (
                                    <p className="text-xs text-gray-600">No data — click Sync to load</p>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                {/* Granularity toggle */}
                                <div className="flex rounded-md overflow-hidden border border-gray-600">
                                    {["hour", "day"].map(g => (
                                        <button
                                            key={g}
                                            onClick={() => setCompletionGranularity(g)}
                                            className={`px-2 py-1 text-xs font-medium transition ${
                                                completionGranularity === g
                                                    ? "bg-blue-600 text-white"
                                                    : "bg-gray-800 text-gray-400 hover:bg-gray-600"
                                            }`}
                                        >
                                            Per {g}
                                        </button>
                                    ))}
                                </div>
                                {/* Window selector */}
                                <div className="flex gap-1">
                                    {WINDOW_OPTIONS.map(days => (
                                        <button
                                            key={days}
                                            onClick={() => setCompletionWindow(days)}
                                            className={`px-2 py-1 rounded text-xs font-medium transition ${
                                                completionWindow === days
                                                    ? "bg-blue-600 text-white"
                                                    : "bg-gray-800 text-gray-400 hover:bg-gray-600"
                                            }`}
                                        >
                                            {days}d
                                        </button>
                                    ))}
                                </div>
                                {/* Sync button */}
                                <button
                                    onClick={syncCompletionData}
                                    disabled={completionSyncing}
                                    className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-600 border border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                >
                                    <RefreshCw size={12} className={completionSyncing ? "animate-spin" : ""} />
                                    {completionSyncing ? "Syncing…" : "Sync"}
                                </button>
                            </div>
                        </div>

                        {!completionData ? (
                            <p className="text-gray-600 text-xs italic">Click Sync to load graph data.</p>
                        ) : completionData.data?.length === 0 ? (
                            <p className="text-gray-500 text-xs">No data for this window.</p>
                        ) : (
                            <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={completionData.data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis
                                        dataKey="timestamp"
                                        tickFormatter={t => formatCompletionTick(t, completionData.granularity)}
                                        tick={{ fill: "#9ca3af", fontSize: 10 }}
                                        interval="preserveStartEnd"
                                        minTickGap={60}
                                    />
                                    <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} width={36} />
                                    <Tooltip
                                        labelFormatter={t => formatCompletionTick(t, completionData.granularity)}
                                        formatter={v => [v.toLocaleString(), "Pages completed"]}
                                        contentStyle={{ backgroundColor: "#1f2937", border: "none", fontSize: 11 }}
                                        labelStyle={{ color: "#e5e7eb" }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="count"
                                        stroke="#22c55e"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        )}

                        {completionData?.data?.length > 0 && (() => {
                            const total = completionData.data.reduce((s, d) => s + d.count, 0);
                            const avg = total / completionData.data.length;
                            return (
                                <p className="text-center text-xs text-gray-400">
                                    Avg&nbsp;
                                    <span className="text-white font-semibold font-mono">{Math.round(avg).toLocaleString()}</span>
                                    &nbsp;pages / {completionGranularity}
                                </p>
                            );
                        })()}
                    </div>
                </div>
                )}
            </div>

            <div className="px-10 py-2 flex flex-col gap-1">
                <div
                    className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
                    onClick={() => setStagesDropdownOpen(!stagesDropdownOpen)}
                >
                    <h2>Stage Status Counts</h2>
                    {stagesDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {stagesDropdownOpen && (
                    <div className="overflow-x-auto rounded-lg">
                        {taskStatusCounts === null ? (
                            <p className="text-gray-400 p-4 text-sm">Loading...</p>
                        ) : (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold sticky left-0 z-10">
                                            Stage
                                        </th>
                                        {STATUS_COLUMNS.map(status => (
                                            <th
                                                key={status}
                                                className="p-2 text-center font-semibold whitespace-nowrap"
                                                style={{ backgroundColor: getStatusColor(status) + "33", color: getStatusColor(status) }}
                                            >
                                                {status}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {stages.map((stage, i) => (
                                        <tr key={stage} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                                            <td className={`p-2 font-semibold text-gray-200 whitespace-nowrap sticky left-0 z-10 ${i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}`}>
                                                {stage}
                                            </td>
                                            {STATUS_COLUMNS.map(status => {
                                                const count = taskStatusCounts[stage]?.[status] ?? 0;
                                                return (
                                                    <td
                                                        key={status}
                                                        className={`p-2 text-center ${count === 0 ? "text-gray-500" : "text-white font-semibold"}`}
                                                    >
                                                        {count.toLocaleString()}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                    <tr className="bg-gray-900 border-t border-gray-600">
                                        <td className="p-2 font-bold text-gray-100 whitespace-nowrap sticky left-0 z-10 bg-gray-900">
                                            TOTAL
                                        </td>
                                        {STATUS_COLUMNS.map(status => {
                                            const total = stages.reduce((sum, stage) => sum + (taskStatusCounts[stage]?.[status] ?? 0), 0);
                                            return (
                                                <td key={status} className={`p-2 text-center font-bold ${total === 0 ? "text-gray-500" : "text-white"}`}>
                                                    {total.toLocaleString()}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>

            <div className="px-10 py-2 flex flex-col gap-1">
                <div
                    className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
                    onClick={() => setModelStatusDropdownOpen(!modelStatusDropdownOpen)}
                >
                    <h2>Model Status Counts</h2>
                    {modelStatusDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {modelStatusDropdownOpen && (
                    <div className="overflow-x-auto rounded-lg">
                        {modelStatusCounts === null ? (
                            <p className="text-gray-400 p-4 text-sm">Loading...</p>
                        ) : (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold sticky left-0 z-10">
                                            Model
                                        </th>
                                        {STATUS_COLUMNS.map(status => (
                                            <th
                                                key={status}
                                                className="p-2 text-center font-semibold whitespace-nowrap"
                                                style={{ backgroundColor: getStatusColor(status) + "33", color: getStatusColor(status) }}
                                            >
                                                {status}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(modelStatusCounts).map(([model, counts], i) => (
                                        <tr key={model} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                                            <td className={`p-2 font-semibold text-gray-200 whitespace-nowrap sticky left-0 z-10 ${i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}`}>
                                                {model}
                                            </td>
                                            {STATUS_COLUMNS.map(status => {
                                                const count = counts[status] ?? 0;
                                                return (
                                                    <td
                                                        key={status}
                                                        className={`p-2 text-center ${count === 0 ? "text-gray-500" : "text-white font-semibold"}`}
                                                    >
                                                        {count.toLocaleString()}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                    <tr className="bg-gray-900 border-t border-gray-600">
                                        <td className="p-2 font-bold text-gray-100 whitespace-nowrap sticky left-0 z-10 bg-gray-900">
                                            TOTAL
                                        </td>
                                        {STATUS_COLUMNS.map(status => {
                                            const total = Object.values(modelStatusCounts).reduce((sum, counts) => sum + (counts[status] ?? 0), 0);
                                            return (
                                                <td key={status} className={`p-2 text-center font-bold ${total === 0 ? "text-gray-500" : "text-white"}`}>
                                                    {total.toLocaleString()}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>

            <div className="px-10 py-2 flex flex-col gap-1">
                <div
                    className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
                    onClick={() => setBatchDropdownOpen(!batchDropdownOpen)}
                >
                    <h2>Batch Counts by Model</h2>
                    {batchDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {batchDropdownOpen && (
                    <div className="overflow-x-auto rounded-lg">
                        {batchCountsByModel === null ? (
                            <p className="text-gray-400 p-4 text-sm">Loading...</p>
                        ) : (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold sticky left-0 z-10">
                                            Model
                                        </th>
                                        {BATCH_STATUS_COLUMNS.map(status => (
                                            <th
                                                key={status}
                                                className="p-2 text-center font-semibold whitespace-nowrap"
                                                style={{ backgroundColor: BATCH_STATUS_COLORS[status] + "33", color: BATCH_STATUS_COLORS[status] }}
                                            >
                                                {status}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {models.map((model, i) => (
                                        <tr key={model} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                                            <td className={`p-2 font-semibold text-gray-200 whitespace-nowrap sticky left-0 z-10 ${i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}`}>
                                                {model}
                                            </td>
                                            {BATCH_STATUS_COLUMNS.map(status => {
                                                const count = batchCountsByModel[model]?.[status] ?? 0;
                                                return (
                                                    <td
                                                        key={status}
                                                        className={`p-2 text-center ${count === 0 ? "text-gray-500" : "text-white font-semibold"}`}
                                                    >
                                                        {count.toLocaleString()}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>

            <div className="px-10 py-2 flex flex-col gap-1">
                <div
                    className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
                    onClick={() => setRequestsDropdownOpen(!requestsDropdownOpen)}
                >
                    <h2>Requests per Batch</h2>
                    {requestsDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {requestsDropdownOpen && (
                    <div className="overflow-x-auto rounded-lg">
                        {requestsCountPerBatch === null ? (
                            <p className="text-gray-400 p-4 text-sm">Loading...</p>
                        ) : (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold">Batch ID</th>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold">Model</th>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold">Status</th>
                                        <th className="text-right p-2 bg-gray-900 text-gray-300 font-semibold">Requests</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {[...requestsCountPerBatch].sort((a, b) => (BATCH_STATUS_ORDER[a.status] ?? 99) - (BATCH_STATUS_ORDER[b.status] ?? 99)).map((batch, i) => (
                                        <tr key={batch.batch_id} className={i % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                                            <td className="p-2 text-gray-400 font-mono">{batch.batch_id}</td>
                                            <td className="p-2 text-gray-200">{batch.model_name}</td>
                                            <td className="p-2 font-semibold" style={{ color: BATCH_STATUS_COLORS[batch.status] ?? "#6b7280" }}>
                                                {batch.status}
                                            </td>
                                            <td className="p-2 text-right text-white font-semibold">{batch.requests_count?.toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>

            <div className="px-10 py-2 flex flex-col gap-1">
                <div
                    className="flex justify-between items-center p-2 bg-gray-900 rounded-lg cursor-pointer"
                    onClick={() => setFailedTasksDropdownOpen(!failedTasksDropdownOpen)}
                >
                    <h2>Failed Tasks by Document</h2>
                    {failedTasksDropdownOpen ? <ChevronUp /> : <ChevronDown />}
                </div>

                {failedTasksDropdownOpen && (
                    <div className="flex flex-col gap-2">
                        {failedTasksByDocument !== null && Object.keys(failedTasksByDocument).length > 0 && (() => {
                            const messageCounts = {};
                            Object.values(failedTasksByDocument).forEach(doc =>
                                doc.failed_tasks.forEach(t => {
                                    const key = t.failure_message ?? "(no message)";
                                    messageCounts[key] = (messageCounts[key] ?? 0) + 1;
                                })
                            );
                            return (
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(messageCounts).sort((a, b) => b[1] - a[1]).map(([msg, count]) => (
                                        <div key={msg} className="flex items-center gap-1 px-2 py-1 rounded bg-gray-700 text-xs">
                                            <span style={{ color: getStatusColor("FAILED") }} className="font-mono">{msg}</span>
                                            <span className="text-white font-bold">{count}</span>
                                        </div>
                                    ))}
                                </div>
                            );
                        })()}
                    <div className="overflow-x-auto rounded-lg">
                        {failedTasksByDocument === null ? (
                            <p className="text-gray-400 p-4 text-sm">Loading...</p>
                        ) : Object.keys(failedTasksByDocument).length === 0 ? (
                            <p className="text-gray-400 p-4 text-sm">No failed tasks.</p>
                        ) : (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold whitespace-nowrap">Document</th>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold whitespace-nowrap">Stage</th>
                                        <th className="text-left p-2 bg-gray-900 text-gray-300 font-semibold w-full">Failure Message</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(failedTasksByDocument).map(([docId, doc], docIdx) =>
                                        doc.failed_tasks.map((task, taskIdx) => (
                                            <tr key={`${docId}-${taskIdx}`} className={docIdx % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}>
                                                {taskIdx === 0 && (
                                                    <td
                                                        rowSpan={doc.failed_tasks.length}
                                                        className={`p-2 font-semibold text-gray-200 whitespace-nowrap align-top border-r border-gray-600 ${docIdx % 2 === 0 ? "bg-gray-700" : "bg-gray-800"}`}
                                                    >
                                                        {doc.name}
                                                    </td>
                                                )}
                                                <td className="p-2 whitespace-nowrap" style={{ color: getStatusColor("FAILED") }}>
                                                    {task.stage_name}
                                                </td>
                                                <td className="p-2 text-gray-300 font-mono">
                                                    {task.failure_message ?? <span className="text-gray-500 italic">none</span>}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                    </div>
                )}
            </div>
        </div>
    );
}
