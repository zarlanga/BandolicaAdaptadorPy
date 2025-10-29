



####################

# ...existing code...
import os
import time
import logging

import numpy as np
import rtmidi
import sounddevice as sd
import librosa

logging.basicConfig(level=logging.INFO)

print("hello world")

# MIDI I/O
midiout_left = rtmidi.MidiOut()
ports = midiout_left.get_ports()
print("Available MIDI output ports:", ports)

midiin = rtmidi.MidiIn()
ports2 = midiin.get_ports()
print("Available MIDI input ports:", ports2)

# Sample map
sample_map = {
    46: "1_bb2.wav",  # Bb2 = MIDI 46
    53: "2_f2.wav",   # F2  = MIDI 53
    60: "3_c3.wav",   # C3  = MIDI 60
    67: "4_g3.wav",   # G3  = MIDI 67
    74: "5_d4.wav",   # D4  = MIDI 74
    81: "6_a4.wav",   # A4  = MIDI 81
    88: "7_e5.wav",   # E5  = MIDI 88
    95: "8_b5.wav",   # B5  = MIDI 95
    102: "9_f6.wav",  # F6  = MIDI 102
}

# Sample rate used for playback and processing
sr = 44100

# Load samples into memory (numpy arrays)
samples = {}
sample_paths = {}
for midi_note, fname in sample_map.items():
    path = os.path.join("mi_troilo", fname)
    if not os.path.isfile(path):
        logging.warning("Sample not found: %s", path)
        continue
    y, _ = librosa.load(path, sr=sr, mono=True)
    samples[midi_note] = y.astype(np.float32)
    sample_paths[midi_note] = path

# Try optional pysoundtouch for pitch-shifting without duration change
USE_SOUNDTOUCH = False
try:
    # Try multiple possible import names to be flexible
    try:
        from pysoundtouch import SoundTouch as _ST
    except Exception:
        from soundtouch import SoundTouch as _ST  # fallback
    # wrapper using guessed API; we will guard with try/except at call time
    def soundtouch_shift(y, sr, n_steps):
        # create instance (channels=1)
        st = _ST(sr, 1)
        # Most bindings offer set_pitch_semitones or setPitchSemiTones; try both
        try:
            st.set_pitch_semitones(float(n_steps))
        except Exception:
            try:
                st.setPitchSemiTones(float(n_steps))
            except Exception:
                raise RuntimeError("SoundTouch API: set_pitch_semitones not found")

        # feed samples (expect float32)
        st.put_samples(y.astype(np.float32).tobytes())
        # receive processed bytes and convert back to float32 numpy
        processed_bytes = st.receive_samples()
        out = np.frombuffer(processed_bytes, dtype=np.float32)
        return out
    USE_SOUNDTOUCH = True
    logging.info("pysoundtouch detected: using SoundTouch for pitch shifting")
except Exception:
    USE_SOUNDTOUCH = False
    logging.info("pysoundtouch / soundtouch not available; falling back to librosa.pitch_shift")

def apply_pitch_shift(y, sr, n_steps):
    """
    Try SoundTouch if available (preserving duration), else librosa (may change duration).
    """
    if n_steps == 0:
        return y
    if USE_SOUNDTOUCH:
        try:
            out = soundtouch_shift(y, sr, n_steps)
            if out.size > 0:
                return out
        except Exception as e:
            logging.warning("SoundTouch pitch shift failed: %s -- falling back to librosa", e)
    # Fallback: librosa (time-stretch+resample based)
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps).astype(np.float32)

# Simple monophonic voice management:
# current_playing_note holds the midi note number currently sounding (or None)
current_playing_note = None
# lock to avoid races (very small program, using a flag is fine)
# play_buffer keeps the last played samples (for debugging or reuse)
play_buffer = None

def play_midi_note(midi_note):
    global current_playing_note, play_buffer
    if midi_note not in samples:
        # find closest sample if exact not present
        if len(samples) == 0:
            logging.warning("No samples loaded")
            return
        base_note = min(samples.keys(), key=lambda n: abs(n - midi_note))
    else:
        base_note = midi_note
    y = samples[base_note]
    n_steps = midi_note - base_note
    y_shifted = apply_pitch_shift(y, sr, n_steps)
    play_buffer = y_shifted
    # stop any currently playing sound (monophonic behavior)
    sd.stop()
    sd.play(y_shifted, sr)
    current_playing_note = midi_note

def stop_midi_note(midi_note):
    global current_playing_note
    # monophonic: stop if current playing note matches (or stop regardless)
    if current_playing_note == midi_note:
        sd.stop()
        current_playing_note = None
    else:
        # if different note, still stop global output (useful for simple setup)
        sd.stop()
        current_playing_note = None

def cb(msg, port):
    # rtmidi callback receives (message, delta_time)
    try:
        message, delta_time = msg
    except Exception:
        logging.debug("Malformed midi message: %s", msg)
        return
    logging.info("Received message on port %s: %s", port, message)
    if not isinstance(message, (list, tuple)) or len(message) < 3:
        return
    status = message[0] & 0xF0
    note = message[1]
    vel = message[2]
    # Note On with vel > 0
    if status == 0x90 and vel > 0:
        play_midi_note(note)
    # Note Off (0x80) or Note On with vel == 0
    elif status == 0x80 or (status == 0x90 and vel == 0):
        stop_midi_note(note)

# Open all MIDI input ports and keep instances to avoid GC
midiin_instances = []
idx = 0
for device in ports2:
    try:
        logging.info("Opening MIDI input device %s index %d", device, idx)
        mi = rtmidi.MidiIn()
        mi.open_port(idx)
        mi.set_callback(cb, idx)
        midiin_instances.append(mi)
    except Exception as e:
        logging.error("Error opening MIDI input port %d: %s", idx, e)
    idx += 1

print("Program running. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    # cleanup
    sd.stop()
    for mi in midiin_instances:
        try:
            mi.close_port()
        except Exception:
            pass