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

# Carga todos los samples en memoria
samples = {}
sr = 44100
for midi_note, fname in sample_map.items():
    path = os.path.join("mi_troilo", fname)
    y, _ = librosa.load(path, sr=sr)
    samples[midi_note] = y

def play_midi_note(midi_note):
    # Encuentra el sample base más cercano
    base_note = min(samples.keys(), key=lambda n: abs(n - midi_note))
    y = samples[base_note]
    n_steps = midi_note - base_note  # diferencia en semitonos

    # Aplica pitch shift si es necesario
    if n_steps != 0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

    sd.play(y, sr)
    #sd.wait()




"""
pathNota = "mi_troilo/2_f2.wav"


y, sr = librosa.load(pathNota, sr=44100)

sd.play(y, sr)
sd.wait()
print("Playing sound...")

y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=4)



sd.play(y_shifted, sr)
sd.wait()
print("Playing shifted sound...")

"""

def cb(msg,port):
        print(f"Received message on port {port}: {msg}")
        message, delta_time = msg
        #midiout_left.send_message(message)
        if len(message) >= 3 and (message[0] & 0xF0) == 0x90 and message[2] > 0:
            midi_note = message[1]
            play_midi_note(midi_note)
        elif len(message) >= 3 and ( 

            ((message[0] & 0xF0) == 0x80) or
            ((message[0] & 0xF0) == 0x90 and message[2] == 0)

            ):
            print("Stopping sound")
            
            sd.stop()


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
