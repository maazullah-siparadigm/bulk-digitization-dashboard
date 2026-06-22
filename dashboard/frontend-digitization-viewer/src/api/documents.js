import { apiFetch } from "./api";

export const getDocuments = async (page = 1, pageSize = 50) => {
  return await apiFetch(`/all_documents?page=${page}&page_size=${pageSize}`);
};


export const getDocumentInfo = async (docId) => {
  return await apiFetch(`/document_info/${docId}`);
};


export const setTaskToPending = async (taskID) => {
  return await apiFetch(`/task_status_change`, {
    method: "POST",
    body: {
      taskId: taskID,
      status: "PENDING"
    }
  });
};


export const getTaskData = async (taskID) => {
  return await apiFetch(`/get_stage_data/${taskID}`);

};

export const getDocumentCounts = async () => {
  return await apiFetch("/document_counts");
};

export const getTaskStatusCounts = async () => {
  return await apiFetch("/task_status_counts");
};

export const getBatchCountsByModel = async () => {
  return await apiFetch("/batch_counts_by_model");
};

export const getRequestsCountPerBatch = async () => {
  return await apiFetch("/requests_count_per_batch");
};

export const getFailedTasksByDocument = async () => {
  return await apiFetch("/failed_tasks_by_document");
};

const TOKEN_ANALYSIS_TIMEOUT = 300_000; // 5 minutes — queries up to 900k rows

export const getTokenAggregates = async (groupBy = "model") => {
  return await apiFetch(`/token_aggregates?group_by=${groupBy}`, { timeout: TOKEN_ANALYSIS_TIMEOUT });
};

export const getTokenHistograms = async (groupBy) => {
  return await apiFetch(`/token_histograms?group_by=${groupBy}`, { timeout: TOKEN_ANALYSIS_TIMEOUT });
};

export const getTokenAggregatesByAgentModel = async () => {
  return await apiFetch(`/token_aggregates_by_agent_model`, { timeout: TOKEN_ANALYSIS_TIMEOUT });
};

export const getCompletedPagesOverTime = async (windowDays, granularity) => {
  return await apiFetch(`/completed_pages_over_time?window_days=${windowDays}&granularity=${granularity}`);
};
