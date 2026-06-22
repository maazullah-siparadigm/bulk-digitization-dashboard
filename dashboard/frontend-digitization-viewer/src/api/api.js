// api.js


const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL; // your backend URL

// Generic fetch function
export const apiFetch = async (
  endpoint,
  { method = "GET", body, headers = {}, timeout, ...fetchOptions} = {}
) => {

  const isFormData = body instanceof FormData;

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      // ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    ...(timeout ? { signal: AbortSignal.timeout(timeout) } : {}),
    ...fetchOptions
  });

  
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || data?.message || `HTTP error ${res.status}`);
  }

  return data;
};