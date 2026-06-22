"use client";

export default function ReenqueueModal({ taskName, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">

        {/* Header */}
        <h2 className="text-lg font-semibold text-gray-900">Re-enqueue Task?</h2>
        <p className="text-sm text-gray-500 mt-1">
          {taskName && <span className="font-medium text-gray-700">"{taskName}"</span>}
        </p>

        {/* Info */}
        <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800 space-y-2">
          <p>Re-enqueuing will set the status of the task to PENDING again, making it available to the orchestrator again.</p>
          <ul className="list-disc list-inside space-y-1 text-amber-700">
            <li>Any tasks that have descended from this task will be invalidated, all the task outputs will be cleared.</li>
            <li>Previously computed data and extracted results from this task and onwards will be cleared</li>
          </ul>
        </div>

        <p className="mt-4 text-sm text-gray-600">Are you sure you want to re-enqueue this task?</p>

        {/* Actions */}
        <div className="mt-5 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm rounded-lg bg-amber-500 text-white font-medium hover:bg-amber-600 transition-colors"
          >
            Yes, Re-enqueue
          </button>
        </div>

      </div>
    </div>
  );
}