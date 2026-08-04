// Thin wrapper over the JSON API. Every action returns the freshly computed
// view model, so the caller never has to guess what changed.

const JSON_HEADERS = { "Content-Type": "application/json" };

export async function fetchState() {
  const res = await fetch("/api/state", { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`Could not load state (${res.status})`);
  return res.json();
}

export async function post(action, payload = {}) {
  const res = await fetch(`/api/${action}`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`${action} failed (${res.status})`);
  return res.json();
}

// Fire-and-forget heartbeat for the running timers; a dropped one is harmless.
export function ping(action, payload = {}) {
  fetch(`/api/${action}`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {});
}
