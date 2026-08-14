// Ambient background sound for Focus sessions. Everything here is
// synthesized with the Web Audio API — no audio files to ship or fetch, so
// it works completely offline like the rest of the app.
//
// Preference (kind + volume) is remembered in localStorage only; it's a
// per-browser listening preference, not app data worth round-tripping
// through the server's JSON store.

const STORAGE_KEY = "uniflow.ambient";

export const AMBIENT_OPTIONS = [
  { value: "none", label: "Off" },
  { value: "brown", label: "White Noise" },
  { value: "pink", label: "Pink Noise" },
  { value: "rain", label: "Rain" },
];

let ctx = null;
let gainNode = null; // master gain for whatever is currently playing
let cleanup = () => {};
let currentKind = "none";

function loadPrefs() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    return {
      kind: AMBIENT_OPTIONS.some((o) => o.value === raw.kind) ? raw.kind : "none",
      volume: typeof raw.volume === "number" ? Math.min(1, Math.max(0, raw.volume)) : 0.4,
    };
  } catch {
    return { kind: "none", volume: 0.4 };
  }
}

function savePrefs(prefs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

let prefs = loadPrefs();

function ensureContext() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
  return ctx;
}

// Builds a few seconds of noise once and loops it, rather than streaming
// samples continuously — much cheaper on the main thread.
function noiseBuffer(context, colour) {
  const seconds = 4;
  const buffer = context.createBuffer(1, context.sampleRate * seconds, context.sampleRate);
  const data = buffer.getChannelData(0);

  if (colour === "white") {
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    return buffer;
  }

  if (colour === "pink") {
    // Voss-McCartney algorithm: sum a handful of white-noise generators that
    // each update at half the rate of the last, producing the -3dB/octave
    // rolloff that distinguishes pink from white/brown noise.
    const rows = new Array(7).fill(0);
    let runningSum = 0;
    for (let i = 0; i < data.length; i++) {
      let rowIndex = 0;
      let n = i + 1;
      while (n % 2 === 0 && rowIndex < rows.length - 1) {
        n /= 2;
        rowIndex += 1;
      }
      runningSum -= rows[rowIndex];
      rows[rowIndex] = Math.random() * 2 - 1;
      runningSum += rows[rowIndex];
      data[i] = (runningSum / rows.length) * 1.8;
    }
    return buffer;
  }

  // "brown": a running sum of white noise (brownian motion), normalised so
  // it doesn't drift out of range.
  let lastOut = 0;
  for (let i = 0; i < data.length; i++) {
    const white = Math.random() * 2 - 1;
    lastOut = (lastOut + 0.02 * white) / 1.02;
    data[i] = lastOut * 3.5;
  }
  return buffer;
}

// Plays a looping noise buffer. The exposed "White Noise" option is actually
// brown noise run through a lowpass filter — raw white/brown noise reads as
// harsh static, this sounds soft and rain-like while keeping the label
// listeners expect.
function playNoise(context, master, colour) {
  const source = context.createBufferSource();
  source.buffer = noiseBuffer(context, colour);
  source.loop = true;

  if (colour === "brown") {
    const filter = context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 1800;
    source.connect(filter);
    filter.connect(master);
    source.start();
    return () => {
      source.stop();
      source.disconnect();
      filter.disconnect();
    };
  }

  source.connect(master);
  source.start();
  return () => {
    source.stop();
    source.disconnect();
  };
}

// Bundled rain recording, fetched and decoded once then cached in memory
// (the file never changes, so re-decoding on every play() would be wasted
// work).
const RAIN_URL = "/static/audio/rain.mp3";
let rainBufferPromise = null;

function loadRainBuffer(context) {
  if (!rainBufferPromise) {
    rainBufferPromise = fetch(RAIN_URL)
      .then((response) => response.arrayBuffer())
      .then((arrayBuffer) => context.decodeAudioData(arrayBuffer));
  }
  return rainBufferPromise;
}

async function playRain(context, master) {
  const audioBuffer = await loadRainBuffer(context);
  const source = context.createBufferSource();
  source.buffer = audioBuffer;
  source.loop = true;
  source.connect(master);
  source.start();
  return () => {
    source.stop();
    source.disconnect();
  };
}

// Returns a copy of the current {kind, volume} preference.
export function currentPrefs() {
  return { ...prefs };
}

// Updates and persists playback volume; applies live if something's playing.
export function setVolume(volume) {
  prefs.volume = Math.min(1, Math.max(0, volume));
  savePrefs(prefs);
  if (gainNode) gainNode.gain.value = prefs.volume;
}

// Tears down whatever ambient sound is currently playing, if any.
export function stop() {
  cleanup();
  cleanup = () => {};
  if (gainNode) {
    gainNode.disconnect();
    gainNode = null;
  }
  currentKind = "none";
}

// Stops any current sound and starts the given ambient kind ("none" just stops).
export function play(kind) {
  prefs.kind = kind;
  savePrefs(prefs);
  stop();
  if (kind === "none") return;

  const context = ensureContext();
  if (context.state === "suspended") context.resume();

  const master = context.createGain();
  master.gain.value = prefs.volume;
  master.connect(context.destination);

  if (kind === "rain") {
    // Decoding is async, so there's a brief gap with nothing to clean up yet;
    // if stop()/play() is called again before it resolves, the loaded track
    // is torn down immediately instead of clobbering whatever plays next.
    cleanup = () => {};
    playRain(context, master).then((stopFn) => {
      if (currentKind === kind && gainNode === master) cleanup = stopFn;
      else stopFn();
    });
  } else {
    cleanup = playNoise(context, master, kind);
  }

  gainNode = master;
  currentKind = kind;
}

export function activeKind() {
  return currentKind;
}

// A soft three-note bell (major triad, each note staggered) for the timer
// reaching zero — reuses the shared AudioContext so it works even if no
// ambient sound is currently playing, but doesn't touch ambient's own
// gain/cleanup state.
const CHIME_NOTES = [523.25, 659.25, 783.99]; // C5, E5, G5
const CHIME_NOTE_GAP_S = 0.12;
const CHIME_NOTE_DURATION_S = 1.6;

export function playChime(volume = 0.5) {
  const context = ensureContext();
  if (context.state === "suspended") context.resume();

  CHIME_NOTES.forEach((freq, i) => {
    const start = context.currentTime + i * CHIME_NOTE_GAP_S;
    const osc = context.createOscillator();
    osc.type = "sine";
    osc.frequency.value = freq;

    const gain = context.createGain();
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(volume * 0.5, start + 0.05);
    gain.gain.exponentialRampToValueAtTime(0.001, start + CHIME_NOTE_DURATION_S);

    osc.connect(gain);
    gain.connect(context.destination);
    osc.start(start);
    osc.stop(start + CHIME_NOTE_DURATION_S + 0.1);
  });
}
