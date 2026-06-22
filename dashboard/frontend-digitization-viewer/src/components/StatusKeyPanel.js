import { Panel } from "reactflow";

export function TaskStatusKeyPanel({ statusesList, getStatusColor }) {
  return (
    <Panel position="top-left">
      <div className="bg-gray-800 rounded-lg p-5 shadow-lg text-sm flex flex-col gap-2">
        <strong className="mb-2">Task Status Key</strong>

        <div className="flex flex-row gap-3">
          {statusesList.map((status) => (
            <div key={status} className="flex items-center gap-1">
              {/* Colored square */}
              <div
                style={{
                    width: "10px",           // equivalent of w-40
                    height: "10px",          // equivalent of h-40
                    borderRadius: "4px",      // equivalent of rounded-sm
                    backgroundColor: getStatusColor(status),
                }}
                ></div>

              {/* Status text */}
              <span className="text-white-100">{status}</span>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}