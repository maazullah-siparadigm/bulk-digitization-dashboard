"use client"

import React, { useState } from "react"
import ReactFlow, { Background, Controls } from "reactflow"
import "reactflow/dist/style.css"

import { DocumentStatsPanel } from "./DocumentStatsPanel"
import { TaskStatusKeyPanel } from "./StatusKeyPanel"
import TaskNode from "./TaskNode"
import TerminalNode from "./TerminalNode"
import { getStatusColor } from "@/utils/statusColors"


const nodeTypes = {
  task : TaskNode,
  terminal : TerminalNode
}

function convertTreeToFlow(node, parentId = null, nodes = [], edges = [], depth = 0, yOffset = 0, reenqueueConfirmationCallback, selectedNodeId = null, reenqueueAllPagesCallback) {
  let nodeWidth = 400
  let nodeHeight = 300

  if (node.type === "START" || node.type === "END"){
    nodeWidth = 200;
  }

  const verticalSpacing = 50
  const horizontalSpacing = 450

  const id = node.id

  // --- Step 1: Calculate subtree heights of children ---
  const childSubtreeHeights = node.children.map((child) => {
    const { lastYOffset } = convertTreeToFlow(child, id, [], [], depth + 1, 0, reenqueueConfirmationCallback, selectedNodeId, reenqueueAllPagesCallback)
    return lastYOffset
  })

  const totalChildrenHeight =
    childSubtreeHeights.reduce((sum, h) => sum + h, 0) +
    verticalSpacing * Math.max(0, childSubtreeHeights.length - 1)

  // Node's own height if no children
  const subtreeHeight = Math.max(nodeHeight, totalChildrenHeight)

  // --- Step 2: Position this node vertically centered above its children ---
  const y = childSubtreeHeights.length > 0
    ? yOffset + totalChildrenHeight / 2 - nodeHeight / 2
    : yOffset

  // --- Step 3: Add this node ---
  nodes.push({
    id,
    type: (node.type === "START" || node.type === "END") ? "terminal" : "task",
    data: {
      taskID: node.id,
      label: node.name,
      status: node.status,
      statuscolor: getStatusColor(node.status),
      reenqueueModalToggle: reenqueueConfirmationCallback,
      reenqueueAllPagesCallback: reenqueueAllPagesCallback,
      pageIndex: node.page_index,
      isSelected: selectedNodeId === node.id,
    },
    style: {
      textAlign: "center",
      width: nodeWidth,
    },
    sourcePosition: "right",
    targetPosition: "left",
    position: { x: depth * horizontalSpacing, y },
  })

  // --- Step 4: Add edge from parent ---
  if (parentId) {
    edges.push({ id: `${parentId}-${id}`, source: parentId, target: id })
  }

  // --- Step 5: Recursively place children ---
  let currentYOffset = yOffset
  node.children.forEach((child) => {
    const { lastYOffset: childHeight } = convertTreeToFlow(child, id, nodes, edges, depth + 1, currentYOffset, reenqueueConfirmationCallback, selectedNodeId, reenqueueAllPagesCallback)
    currentYOffset += childHeight + verticalSpacing
  })

  return { nodes, edges, lastYOffset: subtreeHeight }
}


export default function DocumentTree({ docTree, docStats, reenqueueConfirmationCallback, reenqueueAllPagesCallback }) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);

  let nodes = [];
  let edges = [];

  if (docTree && Object.keys(docTree).length > 0) {
    // Document-level subtrees (e.g. build_page_pairs) belong to no single page, so they
    // are laid out after the page lanes instead of inside one of them.
    const pageChildren = docTree.children.filter((c) => !c.document_level)
    const documentLevelChildren = docTree.children.filter((c) => c.document_level)

    const result = convertTreeToFlow({ ...docTree, children: pageChildren }, null, [], [], 0, 0, reenqueueConfirmationCallback, selectedNodeId, reenqueueAllPagesCallback);
    nodes = result.nodes;
    edges = result.edges;

    const pageHeight = result.lastYOffset

    // Each document-level subtree takes the column after everything placed so far, so
    // build_page_pairs, its link agents, then build_cross_page_hierarchy read left to right.
    documentLevelChildren.forEach((child) => {
      const maxDepth = Math.max(...nodes.map((n) => n.position.x)) / 450
      const { lastYOffset: height } = convertTreeToFlow(child, null, [], [], 0, 0, reenqueueConfirmationCallback, selectedNodeId, reenqueueAllPagesCallback)
      convertTreeToFlow(child, null, nodes, edges, maxDepth + 1, Math.max(0, (pageHeight - height) / 2), reenqueueConfirmationCallback, selectedNodeId, reenqueueAllPagesCallback)
      ;(child.source_ids || []).forEach((sourceId) => {
        edges.push({ id: `${sourceId}-${child.id}`, source: sourceId, target: child.id })
      })
    })
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.01}
        maxZoom={2}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => setSelectedNodeId(prev => prev === node.id ? null : node.id)}
        onPaneClick={() => setSelectedNodeId(null)}
      >
        <Background />
        <Controls />
        <DocumentStatsPanel
          docStats={docStats}
        />
        <TaskStatusKeyPanel
          statusesList={["COMPLETED", "MARKED_FOR_PROC", "PROCESSING", "HANDOFF_PENDING", "FAILED", "PENDING", "OTHER"]}
          getStatusColor={getStatusColor}
        />
      </ReactFlow>
    </div>
  )
}
