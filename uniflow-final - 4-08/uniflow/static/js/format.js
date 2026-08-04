const pad = (n) => String(n).padStart(2, "0");

// MM:SS.d (or HH:MM:SS.d) from tenths of a second — the Focus dial format.
export function countdown(remainingDs) {
  const ds = Math.max(0, remainingDs);
  const tenths = ds % 10;
  const totalSeconds = Math.floor(ds / 10);
  const seconds = totalSeconds % 60;
  const minutes = Math.floor(totalSeconds / 60) % 60;
  const hours = Math.floor(totalSeconds / 3600);
  if (hours > 0) return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}.${tenths}`;
  return `${pad(minutes)}:${pad(seconds)}.${tenths}`;
}

// MM:SS (or HH:MM:SS) — the dashboard stopwatch format.
export function clockTime(totalSeconds) {
  const total = Math.max(0, totalSeconds);
  const seconds = total % 60;
  const minutes = Math.floor(total / 60) % 60;
  const hours = Math.floor(total / 3600);
  if (hours > 0) return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  return `${pad(minutes)}:${pad(seconds)}`;
}

export function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}
