
import random
import time
import board
import asyncio
import keypad
from digitalio import DigitalInOut

import usb_midi

from rotary_encoder import RotaryEncoder

import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend

class State():
    def __init__(self) -> None:
        self.value = "ON"
        self.fx_val = 100
        self.midi = adafruit_midi.MIDI(
            midi_in=usb_midi.ports[0],
            in_channel=0,
            midi_out=usb_midi.ports[1],
            out_channel= 0
        )

# ##########################################################
# LED
#

async def blink(state: State):
    led = DigitalInOut(board.GP25)
    led.switch_to_output()

    while True:
        if state.value is "ON":
            led.value = not led.value
            await asyncio.sleep(0.5)
        else:
            if not led.value:
                led.value = 1
            await asyncio.sleep(0)

# ##########################################################
# Rotary Encoder
#

rotaryEncoder = RotaryEncoder(
    board.GP13,
    board.GP14
)

async def rotary_listen(state: State):        
    while True:
        direction = rotaryEncoder.listenToRotation()
        if direction is not None:
            print('on_rotate', direction)
            if direction == "CLOCKWISE":
                state.fx_val = min(127, state.fx_val + 1)
            elif direction == "ANTICLOCKWISE":
                state.fx_val = max(0, state.fx_val - 1)
            state.midi.send(ControlChange(2, state.fx_val))
            print('state.fx_val', state.fx_val)  
        await asyncio.sleep(0)

# ##########################################################
# Button
#

async def button_listen(state: State):

    with keypad.Keys((board.GP15,), value_when_pressed=False) as keys:
        while True:
            event = keys.events.get()
            if event:
                if event.pressed:
                    if state.value is "OFF":
                        state.value = "ON"
                        state.midi.send(ControlChange(1, 1))
                    else:
                        state.value = "OFF"
                        state.midi.send(ControlChange(1, 0))
                    print('new state', state.value)
            await asyncio.sleep(0)

async def main():
    state = State()

    print('main running')
    rotary_task = asyncio.create_task(rotary_listen(state))
    button_task = asyncio.create_task(button_listen(state))
    blink_task = asyncio.create_task(blink(state))
    
    await asyncio.gather(
        rotary_task,
        button_task,
        blink_task
    )

asyncio.run(main())