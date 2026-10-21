export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const token = sessionStorage.getItem('forma-access-token') || '';
  const response = await fetch('/api' + path, {
    method: body === undefined ? 'GET' : 'POST',
    signal,
    headers: {
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message =
        typeof payload.detail === 'string' ? payload.detail : 'Please check the form fields and try again.';
    } catch {
      /* Keep HTTP error. */
    }
    if (response.status === 401)
      message = 'This workspace requires an access token. Open Workspace settings to connect.';
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function download(runId: string, format: string) {
  const token = sessionStorage.getItem('forma-access-token') || '';
  const response = await fetch(`/api/runs/${runId}/export/${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error('Export is unavailable. Wait for the required artifact to complete.');
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `blueprint-${format}.${format === 'markdown' ? 'md' : 'json'}`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
