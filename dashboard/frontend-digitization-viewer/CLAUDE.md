# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start Next.js development server
npm run build    # Production build
npm start        # Start production server
npm run lint     # Run ESLint
```

No test suite is configured.

## Environment

The backend API URL is set in `.env.local`:
```
NEXT_PUBLIC_API_URL=http://<host>:8000/documents
```

## Architecture

**Next.js App Router** with three routes:
- `/` — empty home page
- `/viewer` — main document viewer (primary page)
- `/stats` — metrics dashboard

**Data flow:** `api/` → `app/` pages → `components/`

### API Layer (`src/api/`)
- `api.js` — generic fetch wrapper supporting JSON and FormData payloads
- `documents.js` — domain endpoints: `getDocuments()`, `getDocumentInfo(docId)`, `setTaskToPending(taskID)`, `getTaskData(taskID)`

### Pages (`src/app/`)
All pages use `"use client"`. The viewer page polls `getDocumentInfo` every 5 seconds for live updates.

### Components (`src/components/`)
Core visualization stack:
- **`DocumentTree.js`** — ReactFlow-based interactive tree; recursively converts the API's tree structure into ReactFlow nodes and edges with hierarchical positioning
- **`TaskNode.js`** — custom ReactFlow node with expandable details panel and action toolbar (Re-enqueue, Retry, Prune); status is color-coded
- **`TerminalNode.js`** — leaf node representation
- **`SideBar.js`** — document list; selection drives the viewer's document context
- **`RenenqueueModal.js`** — confirmation dialog before calling `setTaskToPending`

Supporting display components: `DocumentStatsPanel`, `DocumentThumbnail`, `StatusKeyPanel`, `NavBar`, `Metric`.

### Key Patterns
- Path alias `@/` maps to `src/` (configured in `jsconfig.json`)
- Tailwind CSS v4 for all styling; dynamic colors/dimensions use inline styles
- No global state management — state lives in pages and is passed as props/callbacks
- React Compiler is enabled (`next.config.mjs`)
