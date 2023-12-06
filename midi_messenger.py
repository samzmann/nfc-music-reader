import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.control_change import ControlChange
from adafruit_midi.timing_clock import TimingClock


CONTROL_ON_OFF = 1
CONTROL_FX1 = 2
CONTROL_FX2 = 3

VALUE_ON = 1
VALUE_OFF = 0

class MidiMessenger():
    def __init__(self) -> None:
        self.midi = MIDI(
            midi_in=usb_midi.ports[0],
            in_channel=0,
            midi_out=usb_midi.ports[1],
            out_channel= 0
        )
    
    def send_instrument_on(self):
        self.midi.send(ControlChange(CONTROL_ON_OFF, VALUE_ON))

    def send_instrument_off(self):
        self.midi.send(ControlChange(CONTROL_ON_OFF, VALUE_OFF))

    def send_instrument_fx1(self, value: int):
        self.midi.send(ControlChange(CONTROL_FX1, value))
    
    def send_instrument_fx2(self, value: int):
        self.midi.send(ControlChange(CONTROL_FX2, value))

    def is_timing_clock_event(self, midi_message):
        if isinstance(midi_message, TimingClock):
            return True
        else:
            return False