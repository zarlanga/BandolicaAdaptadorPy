print("hello world")


import rtmidi
import time

midiout_left = rtmidi.MidiOut()
ports = midiout_left.get_ports()
#midiout_left.open_port(0)
#midiout_left.open_virtual_port("Bandoneón Left")

print("Available MIDI output ports:", ports)

midiin = rtmidi.MidiIn()
ports2 = midiin.get_ports()

print("Available MIDI input ports:", ports2)


def cb(msg,port):
        print(f"Received message on port {port}: {msg}")
        message, delta_time = msg
        midiout_left.send_message(message)


idx=0

for device in ports2:
    try:
        print("MIDI input device:", device, idx)
        midiin = rtmidi.MidiIn()
        midiin.open_port(idx)
        midiin.set_callback(cb, idx)
    except Exception as e:
        print(f"Error opening MIDI input port {idx}: {e}")
    idx += 1




"""
idx = 0
for device in ports2:
    print("MIDI input device:", device, idx)
    midiin = rtmidi.MidiIn()
    #midiin.open_port(idx)
    #midiout_left.open_port(idx)
    midiin.set_callback(lambda msg, port: 
                        #midiout_left.send_message(msg)
                        print(f"Received message on port {port}: {msg}")
    )
    
    idx += 1
"""
print("Program running. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")

""" 
# Crear puertos virtuales
midiout_left = rtmidi.MidiOut()
midiout_left.open_virtual_port("Bandoneón Left")

midiout_right = rtmidi.MidiOut()
midiout_right.open_virtual_port("Bandoneón Right")

# Redirigir dispositivos físicos (pseudocódigo)
for device in rtmidi.MidiIn().get_ports():
    if "Teclado Físico" in device:
        midiin = rtmidi.MidiIn()
        midiin.open_port(device)
        midiin.set_callback(lambda msg, port: 
            midiout_left.send_message(msg) if port == 0 else midiout_right.send_message(msg)
        )
# Nota: Este es un ejemplo simplificado y puede requerir ajustes según la configuración del sistema.   """ 