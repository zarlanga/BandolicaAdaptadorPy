print("hello world")


import rtmidi
import time

import sounddevice as sd
import librosa



midiout_left = rtmidi.MidiOut()
ports = midiout_left.get_ports()
#midiout_left.open_port(0)
#midiout_left.open_virtual_port("Bandoneón Left")

print("Available MIDI output ports:", ports)

midiin = rtmidi.MidiIn()
ports2 = midiin.get_ports()

print("Available MIDI input ports:", ports2)

from pyo import Server, SfPlayer
# Inicia servidor pyo (baja latencia)
s = Server().boot()
s.start()

import os
import numpy as np

# Mapea nombres de archivo a números de nota MIDI base
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


# Mapa de paths (pyo leerá los archivos directamente)
sample_paths = {k: os.path.join("mi_troilo", v) for k, v in sample_map.items()}

# Voces activas: key = (port_index, midi_note), value = SfPlayer instance
active_players = {}

def play_midi_note(midi_note, port):
    # Encuentra el sample base más cercano
    if len(sample_paths) == 0:
        print("No sample paths available")
        return
    base_note = min(sample_paths.keys(), key=lambda n: abs(n - midi_note))
    path = sample_paths[base_note]
    if not os.path.isfile(path):
        print("Sample file not found: %s", path)
        return
    n_steps = midi_note - base_note
    speed = 2 ** (n_steps / 12.0)  # factor de velocidad para semitonos

    # Si ya hay una voz para esa nota+port, pararla antes
    key = (port, midi_note)
    old = active_players.get(key)
    if old:
        try:
            old.stop()
        except Exception:
            pass

    # Crear y reproducir la voz
    try:
        player = SfPlayer(path, speed=speed, loop=False, mul=0.9).out()
        active_players[key] = player
    except Exception as e:
        print("Failed to play %s: %s", path, e)


def stop_midi_note(midi_note, port):
    key = (port, midi_note)
    player = active_players.pop(key, None)
    if player:
        try:
            player.stop()
        except Exception:
            pass




def cb(msg, port):
    # rtmidi callback receives (message, delta_time)
    try:
        message, delta_time = msg
    except Exception:
        print("Malformed midi message: %s", msg)
        return
    print("Received message on port %s: %s", port, message)
    if not isinstance(message, (list, tuple)) or len(message) < 3:
        return
    status = message[0] & 0xF0
    note = message[1]
    vel = message[2]

    # Note On with vel > 0
    if status == 0x90 and vel > 0:
        play_midi_note(note, port)
    # Note Off (0x80) or Note On with vel == 0
    elif status == 0x80 or (status == 0x90 and vel == 0):
        stop_midi_note(note, port)

idx=0

midiin_instances = [] 


for device in ports2:
    try:
        print("MIDI input device:", device, idx)
        midiin = rtmidi.MidiIn()
        midiin.open_port(idx)
        midiin.set_callback(cb, idx)
        midiin_instances.append(midiin)
    except Exception as e:
        print(f"Error opening MIDI input port {idx}: {e}")
    idx += 1





print("Program running. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
