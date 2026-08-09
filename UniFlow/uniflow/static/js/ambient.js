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
  { value: "white", label: "White Noise" },
  { value: "pink", label: "Pink Noise" },
  { value: "brown", label: "Rain" },
  { value: "lofi", label: "Lo-Fi Music" },
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
    // Paul Kellet's refined pink noise filter.
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < data.length; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.969 * b2 + white * 0.153852;
      b3 = 0.8665 * b3 + white * 0.3104856;
      b4 = 0.55 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.016898;
      const pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
      b6 = white * 0.115926;
      data[i] = pink * 0.11;
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

// Plays a looping noise buffer. "Rain" (brown noise) gets a lowpass filter
// to cut the harsh high-frequency hiss that otherwise reads as radio static,
// leaving the raw White/Pink options untouched since those are labeled as-is.
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

// A mellow two-chord lo-fi pad (Fmaj7 -> Dm7), each note a pair of slightly
// detuned triangle/sine oscillators through a warm lowpass filter. A simple
// boom-bap drum loop joins in a few seconds later, locked to the same grid
// as the chords (12 steps per chord divides LOFI_CHORD_SECONDS exactly) so
// it always lands on the beat instead of drifting against the pad.
const LOFI_CHORDS = [
  [174.61, 220.0, 261.63, 329.63], // F3 A3 C4 E4 (Fmaj7)
  [146.83, 174.61, 220.0, 261.63], // D3 F3 A3 C4 (Dm7)
];
const LOFI_CHORD_SECONDS = 4.5;
const DRUM_START_DELAY_MS = 5000;
const DRUM_STEPS_PER_CHORD = 12;
const DRUM_STEP_SECONDS = LOFI_CHORD_SECONDS / DRUM_STEPS_PER_CHORD;
// 12 sixteenth-ish steps: kick, rest, hat, snare, rest, hat, kick, rest, hat, snare, rest, hat.
const DRUM_PATTERN = ["kick", null, "hat", "snare", null, "hat", "kick", null, "hat", "snare", null, "hat"];
// Drums get the same warm lowpass character as the pad, so they read as
// part of the same recording rather than a separate, brighter layer.
const DRUM_FILTER_FREQ = 3200;

function playKick(context, master, time) {
  const osc = context.createOscillator();
  osc.type = "sine";
  osc.frequency.setValueAtTime(140, time);
  osc.frequency.exponentialRampToValueAtTime(45, time + 0.15);

  const gain = context.createGain();
  gain.gain.setValueAtTime(0.7, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.25);

  osc.connect(gain);
  gain.connect(master);
  osc.start(time);
  osc.stop(time + 0.3);
}

function playHihat(context, master, time) {
  const source = context.createBufferSource();
  source.buffer = noiseBuffer(context, "white");

  const filter = context.createBiquadFilter();
  filter.type = "highpass";
  filter.frequency.value = 6500;

  const gain = context.createGain();
  gain.gain.setValueAtTime(0.09, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.05);

  source.connect(filter);
  filter.connect(gain);
  gain.connect(master);
  source.start(time);
  source.stop(time + 0.06);
}

function playSnare(context, master, time) {
  const source = context.createBufferSource();
  source.buffer = noiseBuffer(context, "white");

  const filter = context.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.value = 1600;

  const warmth = context.createBiquadFilter();
  warmth.type = "lowpass";
  warmth.frequency.value = DRUM_FILTER_FREQ;

  const gain = context.createGain();
  gain.gain.setValueAtTime(0.3, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);

  source.connect(filter);
  filter.connect(warmth);
  warmth.connect(gain);
  gain.connect(master);
  source.start(time);
  source.stop(time + 0.16);
}

// A short dip in the pad's own gain on every kick — the "sidechain pump"
// that glues drums and chords together in the same mix instead of sounding
// like two unrelated loops layered on top of each other.
function duckChords(context, chordBus, time) {
  const gain = chordBus.gain;
  const current = gain.value;
  gain.cancelScheduledValues(time);
  gain.setValueAtTime(current, time);
  gain.linearRampToValueAtTime(current * 0.55, time + 0.05);
  gain.linearRampToValueAtTime(current, time + 0.3);
}

function playDrums(context, drumBus, chordBus) {
  // Snap the entrance to the next chord downbeat at/after the 5s mark, so
  // the beat always drops in step with the pad rather than mid-bar.
  const chordsSinceStart = Math.ceil(DRUM_START_DELAY_MS / 1000 / LOFI_CHORD_SECONDS);
  const startDelayMs = chordsSinceStart * LOFI_CHORD_SECONDS * 1000;

  let stepIndex = 0;
  let timerId = null;
  const step = () => {
    const hit = DRUM_PATTERN[stepIndex % DRUM_PATTERN.length];
    const time = context.currentTime;
    if (hit === "kick") {
      playKick(context, drumBus, time);
      duckChords(context, chordBus, time);
    } else if (hit === "hat") {
      playHihat(context, drumBus, time);
    } else if (hit === "snare") {
      playSnare(context, drumBus, time);
    }
    stepIndex += 1;
    timerId = setTimeout(step, DRUM_STEP_SECONDS * 1000);
  };
  const startId = setTimeout(step, startDelayMs);

  return () => {
    clearTimeout(startId);
    clearTimeout(timerId);
  };
}

function playLofiChord(context, master, freqs) {
  const now = context.currentTime;
  const nodes = [];
  for (const freq of freqs) {
    const filter = context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 1100;

    const noteGain = context.createGain();
    noteGain.gain.setValueAtTime(0, now);
    noteGain.gain.linearRampToValueAtTime(0.9 / freqs.length, now + 1);
    noteGain.gain.linearRampToValueAtTime(0, now + LOFI_CHORD_SECONDS);

    const osc = context.createOscillator();
    osc.type = "triangle";
    osc.frequency.value = freq;
    const detune = context.createOscillator();
    detune.type = "sine";
    detune.frequency.value = freq * 1.004;

    osc.connect(filter);
    detune.connect(filter);
    filter.connect(noteGain);
    noteGain.connect(master);

    osc.start(now);
    detune.start(now);
    osc.stop(now + LOFI_CHORD_SECONDS + 0.2);
    detune.stop(now + LOFI_CHORD_SECONDS + 0.2);
    nodes.push(filter, noteGain, osc, detune);
  }
  return nodes;
}

function playLofi(context, master) {
  // Separate buses for pad and drums, both feeding the shared master gain,
  // so the kick can duck the pad without touching the drums' own level.
  const chordBus = context.createGain();
  const drumBus = context.createGain();
  chordBus.gain.value = 1;
  drumBus.gain.value = 0.8;
  chordBus.connect(master);
  drumBus.connect(master);

  let chordIndex = 0;
  let chordTimerId = null;
  const stepChords = () => {
    playLofiChord(context, chordBus, LOFI_CHORDS[chordIndex % LOFI_CHORDS.length]);
    chordIndex += 1;
    chordTimerId = setTimeout(stepChords, LOFI_CHORD_SECONDS * 1000);
  };
  stepChords();

  const stopDrums = playDrums(context, drumBus, chordBus);

  return () => {
    clearTimeout(chordTimerId);
    stopDrums();
    chordBus.disconnect();
    drumBus.disconnect();
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

  cleanup = kind === "lofi" ? playLofi(context, master) : playNoise(context, master, kind);

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
