"use client";
import { useState } from "react";
import { Handle, Position, NodeToolbar } from "reactflow";
import { ChevronDown, ChevronUp, Clock, RotateCcw, Scissors } from "lucide-react";
import { getTaskData } from "@/api/documents";
import { getStatusColor } from "@/utils/statusColors";

export default function TaskNode({ data }) {
  const [detailsExpanded, setDetailsExpanded] = useState(false);
  const [taskInformation, setTaskInformation] = useState({});

  async function getCurrentTaskData(e){
        e.stopPropagation();
        if (detailsExpanded) {
            setDetailsExpanded(false);
            return;
        }
        setDetailsExpanded(true);
        const res = await getTaskData(data.taskID);
        if (res){
            setTaskInformation(res);
        }
  }

  return (
    <div
        className={`p-5 w-full h-full border ${data.isSelected ? "border-blue-500 border-1" : "border-blue-100 border-1"} rounded-lg shadow-sm`}
        style={{ backgroundColor: getStatusColor(data.status) }}
    >
        <Handle type="target" position={Position.Left} />
        <Handle type="source" position={Position.Right} />

        <div className="bg-gray-800 rounded-lg py-2">
            {/* Header */}
            <div className="bg-gray-800 flex flex-row justify-between items-center p-1">
                <span className="text-xs">{data.label}</span>
                <div
                    className="bg-gray-600 rounded-md p-1"
                    onClick={getCurrentTaskData}
                    >
                    {detailsExpanded ? <ChevronUp width={25} height={25}/> : <ChevronDown width={25} height={25}/>}
                </div>
            </div>

            {/* Body */}
            {detailsExpanded && (
                <div className="bg-gray-600 h-48 overflow-y-auto p-2 text-sm font-mono text-white text-left">
                    <pre>{JSON.stringify(taskInformation, null, 2)}</pre>
                </div>
            )}

            <div className="bg-gray-800 flex flex-row justify-between px-2">
                <p className="text-sm">Status: {data.status}</p>
                <p className="text-sm">{data.pageIndex}</p>
            </div>
        </div>

        <NodeToolbar
                className='flex flex-col rounded-lg p-2 gap-3 bg-gray-800'
                isVisible={data.isSelected}
                position={Position.Top}
            >
                <button className="flex flex-row gap-1" onClick={() => data?.reenqueueModalToggle({id: data.taskID, taskName: data.label, pageIndex: data.pageIndex})}>
                    <Clock className='w-5 h-5' />
                    <span>Re-enqueue the task</span>
                </button>

                <button className="flex flex-row gap-1" onClick={() => data?.reenqueueAllPagesCallback({id: data.taskID, taskName: data.label})}>
                    <Clock className='w-5 h-5' />
                    <span>Re-enqueue task for all pages</span>
                </button>

                <button className="flex flex-row gap-1">
                    <RotateCcw className='w-5 h-5' />
                    <span>Retry Task</span>
                </button>

                <button className="flex flex-row gap-1">
                    <Scissors className="w-5 h-5"/>
                    <span>Prune</span>
                </button>
        </NodeToolbar>

    </div>
  );
}
