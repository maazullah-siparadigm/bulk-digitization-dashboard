# Frontend Digitization Viewer — Claude Context

This document captures the complete current state of the frontend codebase so a new Claude session can continue work without re-deriving context.

---

## Project Overview

A **Next.js 16** (App Router) dashboard that monitors and controls a document digitization pipeline. The pipeline ingests documents, splits them into pages, and runs each page through a chain of AI agents (bbox extraction, text extraction, table extraction, etc.). The frontend shows real-time pipeline state, lets operators requeue failed tasks, and provides analytics over token consumption and costs.

**Backend** runs at `http://<host>:8000/documents` (set via `NEXT_PUBLIC_API_URL` in `.env.local`). The backend is a separate repo maintained independently.

---

## Tech Stack

| Layer | Library/Version |
|-------|----------------|
| Framework | Next.js 16.1.6, React 19, App Router |
| Styling | Tailwind CSS v4 (no config file — uses `@tailwindcss/postcss`) |
| Flow/Graph | ReactFlow 11.11.4 |
| Charts | Recharts 3.8.1 |
| Icons | lucide-react 0.575.0 |
| Fonts | Geist / Geist Mono (via next/font/google) |
| Compiler | React Compiler enabled in `next.config.mjs` |

**Path alias:** `@/` → `src/`

---

## Directory Structure

```
src/
├── api/
│   ├── api.js              — generic fetch wrapper
│   └── documents.js        — all domain API calls
├── app/
│   ├── layout.js           — root layout (NavBar + <main>)
│   ├── page.js             — empty home page (/)
│   ├── globals.css         — Tailwind base styles
│   ├── stats/page.js       — pipeline metrics dashboard (/stats)
│   ├── token-analysis/page.js — token usage & cost analysis (/token-analysis)
│   └── viewer/page.js      — document tree viewer (/viewer)
├── components/
│   ├── DocumentStatsPanel.js   — ReactFlow Panel overlay with per-doc stats
│   ├── DocumentThumbnail.js    — small card shown in sidebar document list
│   ├── DocumentTree.js         — ReactFlow canvas; converts API tree → nodes/edges
│   ├── Metric.js               — generic metric card (title, value, subtitle)
│   ├── NavBar.js               — top nav with links to Stats / Viewer / Token Analysis
│   ├── SideBar.js              — collapsible doc list (left panel in Viewer)
│   ├── StatusKeyPanel.js       — status colour legend in ReactFlow canvas
│   ├── TaskNode.js             — custom ReactFlow node; expandable details + toolbar
│   ├── TerminalNode.js         — START/END node type in ReactFlow
│   └── modals/
│       └── RenenqueueModal.js  — confirmation dialog before re-enqueuing a task
└── utils/
    └── statusColors.js     — maps status string → hex colour
```

---

## API Layer

### `src/api/api.js`

Generic fetch wrapper. Supports JSON and FormData bodies.

```js
export const apiFetch = async (
  endpoint,
  { method = "GET", body, headers = {}, timeout, ...fetchOptions } = {}
) => { ... }
```

- Prepends `NEXT_PUBLIC_API_URL` to every endpoint.
- `timeout` uses `AbortSignal.timeout(ms)` — only applied when passed explicitly.
- Throws on non-2xx responses using `data.detail || data.message || HTTP error ${status}`.

### `src/api/documents.js`

All API calls. **Important constant:**

```js
const TOKEN_ANALYSIS_TIMEOUT = 300_000; // 5 minutes — queries ~900k rows
```

| Function | Endpoint | Notes |
|----------|----------|-------|
| `getDocuments(page, pageSize)` | `GET /all_documents?page=&page_size=` | Returns `{ documents: [], total: int }` |
| `getDocumentInfo(docId)` | `GET /document_info/:docId` | Returns `{ docTree, docStats }` |
| `setTaskToPending(taskID)` | `POST /task_status_change` | Body: `{ taskId, status: "PENDING" }` |
| `getTaskData(taskID)` | `GET /get_stage_data/:taskID` | Returns raw task data as JSON |
| `getDocumentCounts()` | `GET /document_counts` | Returns counts object (see shape below) |
| `getTaskStatusCounts()` | `GET /task_status_counts` | Returns `{ STAGE_NAME: { STATUS: count } }` |
| `getBatchCountsByModel()` | `GET /batch_counts_by_model` | Returns `{ model_name: { STATUS: count } }` |
| `getRequestsCountPerBatch()` | `GET /requests_count_per_batch` | Returns array of `{ batch_id, model_name, status, requests_count }` |
| `getFailedTasksByDocument()` | `GET /failed_tasks_by_document` | Returns `{ docId: { name, failed_tasks: [{ stage_name, failure_message }] } }` |
| `getTokenAggregates(groupBy)` | `GET /token_aggregates?group_by=model\|agent` | Has 5-min timeout |
| `getTokenHistograms(groupBy)` | `GET /token_histograms?group_by=model\|agent` | Has 5-min timeout |
| `getTokenAggregatesByAgentModel()` | `GET /token_aggregates_by_agent_model` | Has 5-min timeout |
| `getCompletedPagesOverTime(windowDays, granularity)` | `GET /completed_pages_over_time?window_days=&granularity=hour\|day` | No timeout |

#### `getDocumentCounts()` expected response shape
```json
{
  "total": 1234,
  "completed": 987,
  "digitization_failed": 45,
  "total_pages": 56789,
  "completed_pages": 43210,
  "failed_pages": 2100
}
```
*(The `total_pages`, `completed_pages`, `failed_pages` fields may need to be added to the backend if not yet implemented.)*

#### `getTokenAggregatesByAgentModel()` expected response shape
```json
{
  "BBOX_AGENT": {
    "gemini-3-flash-preview": {
      "input_tokens": 1234567,
      "output_tokens": 89012,
      "thinking_tokens": 0
    }
  },
  "TEXT_EXTRACTION_AGENT": { ... }
}
```
Keys are uppercase stage names. Each agent maps to one or more models (typically one from config). This endpoint was specifically added to enable per-agent cost calculation on the frontend.

#### `getCompletedPagesOverTime()` expected response shape
```json
{
  "granularity": "hour",
  "data": [
    { "timestamp": "2026-06-15T14:00:00Z", "count": 342 },
    { "timestamp": "2026-06-15T15:00:00Z", "count": 519 }
  ]
}
```
Zero-filled buckets expected. The `granularity` field in the response is used by the frontend to format axis labels correctly.

---

## Pages

### `/stats` — `src/app/stats/page.js`

The main metrics dashboard. All data polled every **15 seconds** (except completion graph — see below).

#### Key state

| State variable | Type | Purpose |
|----------------|------|---------|
| `docMetrics` | object | Document-level metrics (total, completed, failed) |
| `pageMetrics` | object | Page-level metrics (total_pages, completed_pages, failed_pages) |
| `taskStatusCounts` | object | Stage → status → count |
| `batchCountsByModel` | object | Model → batch status → count |
| `requestsCountPerBatch` | array | Per-batch request counts |
| `failedTasksByDocument` | object | Doc → failed task list |
| `completionWindow` | number (1/2/3/5/7) | Days window for graph |
| `completionGranularity` | "hour"\|"day" | Graph granularity |
| `completionData` | object\|null | Cached graph data from localStorage |
| `completionFetchedAt` | ISO string\|null | When graph data was last fetched |
| `completionSyncing` | boolean | True while graph fetch is in-flight |
| `modelStatusCounts` | derived (IIFE) | Grouped by model name from `taskStatusCounts` |

#### `STAGE_TO_MODEL` constant
Maps pipeline stage names to model names. Used to build the "Model Status Counts" section. Stages not listed fall under `"other"`.

```js
const STAGE_TO_MODEL = {
  "BBOX_AGENT":                  "gemini-3-flash-preview",
  "SECTION_SPAN_AGENT":          "gemini-2.5-flash",
  "TEXT_EXTRACTION_AGENT":       "gemini-2.5-flash",
  "MARGINALIA_EXTRACTION_AGENT": "gemini-2.5-flash",
  "TABLE_VERIFICATION_AGENT":    "gemini-2.5-flash",
  "TABLE_EXTRACTION_AGENT":      "gemini-3.5-flash",
  "IMAGE_EXTRACTION_AGENT":      "gemini-2.5-flash",
};
```

#### Status columns used in tables
```js
const STATUS_COLUMNS = [
  "PENDING", "MARKED_FOR_PROC", "SUBMITTED", "STARTED",
  "PROCESSING", "HANDOFF_PENDING", "COMPLETED", "FAILED",
];

const BATCH_STATUS_COLUMNS = [
  "PENDING", "SUBMITTED", "COMPLETED", "FAILED", "CANCELLED", "EXPIRED",
];
```

#### Completion graph — localStorage cache
The graph does **not** auto-fetch. The user must click **Sync** manually. Data is stored in `localStorage` under key `"completion_pages_cache"` as:

```json
{
  "7_day":  { "data": { ... }, "fetchedAt": "2026-06-22T10:00:00.000Z" },
  "1_hour": { "data": { ... }, "fetchedAt": "2026-06-22T09:00:00.000Z" }
}
```

When the user changes `completionWindow` or `completionGranularity`, the page reads from this cache (no network call). When the user clicks Sync, fresh data is fetched, the cache entry for the current `window_granularity` key is updated, and the UI reflects the new `fetchedAt` timestamp.

Helper functions inside the component (not exported):
- `getCompletionCacheEntry(window, granularity)` — reads from localStorage
- `setCompletionCacheEntry(window, granularity, data)` — writes and returns the entry
- `syncCompletionData()` — async, calls the API and updates state + cache

#### Collapsible sections (in render order)
1. **Metrics** — doc metrics row (3 cards) + page metrics row (3 cards) + completion line graph
2. **Stage Status Counts** — full stage × status table with TOTAL row
3. **Model Status Counts** — derived from Stage counts, grouped by model via STAGE_TO_MODEL
4. **Batch Counts by Model** — batch status breakdown per model
5. **Requests per Batch** — sorted by batch status order
6. **Failed Tasks by Document** — failure message summary chips + full table

All count/total values in tables use `.toLocaleString()` for comma-formatted numbers.
Metric card numbers also use `.toLocaleString()`.
Completed/Failed metrics show a subtitle `"X.X% of total"`.

---

### `/token-analysis` — `src/app/token-analysis/page.js`

Token usage and cost analytics. **No auto-polling.** All data is manually fetched and cached to `localStorage` under key `"token_analysis_data"`.

#### Data fetched (all in parallel via `Promise.all`)
1. `getTokenAggregates("model")` → totals bar chart data
2. `getTokenAggregates("agent")` → stored but not currently used in totals (histograms handle agent grouping)
3. `getTokenHistograms("model")` → per-model token distribution histograms
4. `getTokenHistograms("agent")` → per-agent token distribution histograms
5. `getTokenAggregatesByAgentModel()` → per-agent cost calculation

#### localStorage shape
```json
{
  "aggregates": {
    "model": { "gemini-2.5-flash": { "input_tokens": ..., "output_tokens": ..., "thinking_tokens": ... } },
    "agent": { "BBOX_AGENT": { ... } }
  },
  "histograms": {
    "model": { "gemini-2.5-flash": { "input_tokens": [{ "bin_start": 0, "bin_end": 1000, "count": 42 }], ... } },
    "agent": { ... }
  },
  "agentModelBreakdown": {
    "BBOX_AGENT": { "gemini-3-flash-preview": { "input_tokens": ..., ... } }
  },
  "fetchedAt": "2026-06-22T10:00:00.000Z"
}
```

#### `MODEL_PRICING` constant (price per 1M tokens in USD)
```js
const MODEL_PRICING = {
  "gemini-3.5-flash":      { input: 0.75,  output: 4.5,  thinking: 4.5  },
  "gemini-2.5-flash":      { input: 0.15,  output: 1.25, thinking: 1.25 },
  "gemini-2.5-flash-lite": { input: 0.05,  output: 0.20, thinking: 0.20 },
  "gemini-3-flash-preview":{ input: 0.25,  output: 1.50, thinking: 1.50 },
};
```
Models not in the dict get zero cost. Update this dict as pricing changes.

#### `calculateCost(model, inputTokens, outputTokens, thinkingTokens)`
Returns `{ input, output, thinking, total }` in USD.

#### Collapsible sections
1. **Token Totals** — grouped bar chart (by model, showing input/output/thinking tokens side by side). No By Model/By Agent toggle — always shows model view.
2. **Token Distribution** — histogram per group (model or agent), toggled by "By Model / By Agent" selector. Each group shows 3 histograms (input, output, thinking) plus stat strip (n, mean, median, mode, σ).
3. **Token Pricing** — table toggled by "By Model / By Agent":
   - **By Model**: columns = Model | Input Tokens | Output Tokens | Thinking Tokens | Input Cost | Output Cost | Thinking Cost | Total Cost
   - **By Agent**: same columns but first column is Agent; costs are summed across all models the agent used

#### Timestamp display
Header shows "Last fetched: Xm ago / Xh ago / just now" via `formatTimestamp(iso)`.

---

### `/viewer` — `src/app/viewer/page.js`

Document tree viewer with sidebar and re-enqueue modal.

- Fetches paginated document list (50 per page) on load and page change.
- On document selection, fetches `getDocumentInfo(docId)` and polls every **5 seconds**.
- `docTree` is passed to `DocumentTree` which renders it as a ReactFlow graph.
- `docStats` is displayed in `DocumentStatsPanel` (top-right panel overlay).
- Selecting a node in the tree shows a `NodeToolbar` with Re-enqueue / Re-enqueue all pages / Retry / Prune actions.
- Re-enqueue opens `ReenqueueModal` for confirmation, then calls `setTaskToPending(taskID)`.
- `reenqueueAllPagesCallback` is wired up but **not implemented** (TODO).

---

## Components

### `Metric.js`
```jsx
<Metric title="Total Pages" value="56,789" subtitle="12.3% of total" />
```
Props: `title` (always shown), `value` (optional), `subtitle` (optional, smaller gray text below value).

### `DocumentTree.js`
Converts the backend's nested tree structure into ReactFlow nodes and edges via `convertTreeToFlow()` — a recursive function that:
- Calculates subtree heights first (pass 1) to vertically centre parent nodes
- Places nodes at `x = depth * 450`, `y = computed vertical centre`
- START/END nodes use type `"terminal"` (width 200); all others use type `"task"` (width 400)
- Creates edges as `{ id: "parentId-childId", source: parentId, target: childId }`

### `TaskNode.js`
Custom ReactFlow node. Clicking the chevron expands a details panel showing raw `getTaskData()` response as pretty-printed JSON. The `NodeToolbar` is shown when the node is selected (click node to select, click again or click canvas to deselect).

**Toolbar buttons:**
- Re-enqueue the task (calls `reenqueueModalToggle`)
- Re-enqueue task for all pages (calls `reenqueueAllPagesCallback` — not yet implemented)
- Retry Task (button exists, no handler)
- Prune (button exists, no handler)

### `StatusKeyPanel.js`
ReactFlow `Panel` component (bottom-left) showing coloured status legend dots.

### `DocumentStatsPanel.js`
ReactFlow `Panel` component (top-right) showing per-document stats: numPages, totalTasks, numCompleted, numPending, numFailed, numAgenticCalls. Collapsible via ▴/▾ button.

### `SideBar.js`
Collapsible (ChevronLeft/Right toggle) document list. Renders `DocumentThumbnail` per document. Has pagination controls showing `currentPage / totalPages`.

### `NavBar.js`
Three links: Stats (`/stats`), Document Viewer (`/viewer`), Token Analysis (`/token-analysis`). The `activePage` prop for highlighting is passed in but the `onClick` handler is commented out — highlighting doesn't work currently (minor UI issue, not blocking).

### `ReenqueueModal.js`
Confirmation dialog. Shows amber warning box explaining consequences of re-enqueuing. Two buttons: Cancel and "Yes, Re-enqueue".

---

## `utils/statusColors.js`

```js
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
```

---

## Known Bugs / Pending Work

### 1. Completion graph granularity toggle (UNRESOLVED BUG)
**Symptom:** Toggling between "Per hour" and "Per day" on the completion graph in Stats does nothing — the graph and average don't change.

**Root cause:** The backend endpoint `GET /documents/completed_pages_over_time` may not exist yet. The toggle itself is correctly wired (changing `completionGranularity` state triggers the cache lookup useEffect, and clicking Sync would call `getCompletedPagesOverTime(window, granularity)`). The most likely cause is that the backend isn't implemented, so all fetch attempts silently fail.

**Fix path:** Once the backend endpoint is implemented, clicking Sync with different granularity values should produce different results. No frontend code changes needed.

### 2. Backend endpoints that may not be implemented yet
These were designed during this session and the backend Claude was asked to implement them in a separate chat:

| Endpoint | Status |
|----------|--------|
| `GET /documents/completed_pages_over_time?window_days=&granularity=` | Needs backend implementation |
| `GET /documents/token_aggregates_by_agent_model` | Confirmed implemented by backend (uppercase stage keys, one model per agent from config) |
| `GET /documents/document_counts` fields `total_pages`, `completed_pages`, `failed_pages` | May need to be added to existing endpoint |

### 3. `reenqueueAllPagesCallback` not implemented
`TaskNode` has a "Re-enqueue task for all pages" button that calls `reenqueueAllPagesCallback` but the viewer page has an empty implementation (`// TODO: implement re-enqueue for all pages`).

### 4. NavBar active page highlighting
`activePage` prop is passed to NavBar but the `onClick` that would set it is commented out. Nav links work (Next.js `<Link>`), but the active styling doesn't apply.

### 5. Retry and Prune buttons in TaskNode toolbar
Both buttons exist in the `NodeToolbar` but have no `onClick` handlers.

---

## Patterns & Conventions

- All pages use `"use client"`.
- **No global state** — everything lives in page-level `useState`, passed down as props/callbacks.
- Tailwind dark theme: `bg-gray-900` (darkest) → `bg-gray-800` → `bg-gray-700` (lightest panels). Alternating table rows use `bg-gray-700` / `bg-gray-800`.
- Dynamic colors and pixel-based dimensions use inline `style={}` props, not Tailwind.
- Numbers in tables and metric cards always use `.toLocaleString()` for comma formatting.
- Costs displayed as `$X.XXXX` (4 decimal places via `.toFixed(4)`).
- Token counts in histograms use `formatTokenCount(n)` which returns `"1.2M"`, `"500K"`, or `"42"`.
- Collapsible sections use `ChevronUp`/`ChevronDown` icons from lucide-react with a `useState` boolean toggle.
- `e.stopPropagation()` is used inside collapsible content areas that have `onClick` on the container.
- Long-running API calls (token analysis) use `AbortSignal.timeout(300_000)` via the `timeout` option in `apiFetch`.
- localStorage is used to persist expensive data across page reloads (token analysis data and completion graph data).

---

## Environment

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://<host>:8000/documents
```

```bash
npm run dev    # Next.js dev server
npm run build  # Production build
npm start      # Production server
npm run lint   # ESLint
```

No test suite is configured.
