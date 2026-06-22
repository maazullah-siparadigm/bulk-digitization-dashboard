"use client";
import { Handle, Position } from "reactflow";
import { getStatusColor } from "@/utils/statusColors";

export default function TerminalNode({ data }) {
  return (
    <div
        className="p-5 w-full h-full border border-gray-200 rounded-full shadow-sm"
        style={{ backgroundColor: getStatusColor(data.status) }}
    >
        <Handle type="target" position={Position.Left} />
        <Handle type="source" position={Position.Right} />

        <div className="bg-gray-800 rounded-full py-2">
            <span className="text-xs">{data.label}</span>
            <p className="text-sm">Status: {data.status}</p>
        </div>
    </div>
  );
}
