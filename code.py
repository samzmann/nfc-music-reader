import asyncio
import board
import time
from digitalio import DigitalInOut
from adafruit_simplemath import map_range

from effect_control import EffectControl
from rotary_encoder import RotaryEncoder
from main_display import MainDisplay
from led_manager import LedManager, POSSIBLE_LED_STATES
from nfc_reader import NfcReader
from midi_messenger import MidiMessenger
from bpm_tracker import BPMTracker

# ##########################################################
# ControllerData
#

class ControllerData():
    def __init__(self):

        self.instrument_on = False
        self.fx1_value = 100
        self.fx2_value = 100

        self.led_on = False
        self.led_turned_on = False
        self.led_on_timestamp = 0

# ##########################################################
# MIDI
#

midi_messenger = MidiMessenger()
bpm_tracker = BPMTracker()

async def midi_listen(controllerData: ControllerData):
    while True:
        msg = midi_messenger.midi.receive()
        if msg is not None:
            print("Received:", msg, "at", time.monotonic())
            if midi_messenger.is_timing_clock_event(msg):
                bpm_tracker.add_timestamp(time.monotonic())
                bpm = bpm_tracker.calculate_bpm()
                print('bpm', bpm)
                controllerData.led_on = True
        await asyncio.sleep(0)

async def blink_beat(controllerData: ControllerData):
    led = DigitalInOut(board.GP25)
    led.switch_to_output()

    while True:
        if controllerData.led_on and controllerData.led_turned_on == False:
            led.value = 1
            controllerData.led_turned_on = True
            controllerData.led_on_timestamp = time.monotonic()
        if controllerData.led_on and time.monotonic() > controllerData.led_on_timestamp + 0.1:
            led.value = 0
            controllerData.led_on = False
            controllerData.led_turned_on = False
        await asyncio.sleep(0)



# ##########################################################
# Display
#

mainDisplay = MainDisplay()


# ##########################################################
# Rotary Encoder
#

rotaryEncoder = RotaryEncoder(
    board.GP13,
    board.GP14
)

FX_1_INCREMENT = 5

async def rotary_listen(controllerData: ControllerData):        
    while True:
        direction = rotaryEncoder.listenToRotation()
        
        if direction is not None:
            if direction == "CLOCKWISE":
                controllerData.fx1_value = min(127, controllerData.fx1_value + FX_1_INCREMENT)
            elif direction == "ANTICLOCKWISE":
                controllerData.fx1_value = max(0, controllerData.fx1_value - FX_1_INCREMENT)
            midi_messenger.send_instrument_fx1(controllerData.fx1_value)
            mainDisplay.set_text_area_value('fx_1', controllerData.fx1_value)
        await asyncio.sleep(0)

# ##########################################################
# Effect controls (potentiometers and other analog input devices)
#

fx2 = EffectControl(board.GP28, 200, 65000)

async def poll_effect_controls(controllerData: ControllerData):
    while True:
        value = fx2.get_value()
        mapped_value = round(map_range(value, 0, 65535, 0, 127))
        if mapped_value != controllerData.fx2_value:
            controllerData.fx2_value = mapped_value
            midi_messenger.send_instrument_fx2(controllerData.fx2_value)
            mainDisplay.set_text_area_value('fx_2', controllerData.fx2_value)
        await asyncio.sleep(0.1)

# ##########################################################
# LED Manager
#

led_manager = LedManager()

async def run_led_animations():
    while True:
        led_manager.animate()
        await asyncio.sleep(0)

# ##########################################################
# NFC
#

def on_card_detected():
    midi_messenger.send_instrument_on()
    led_manager.transition(POSSIBLE_LED_STATES["LIVE"])
    mainDisplay.set_text_area_value('state', "ON")

def on_card_removed():
    midi_messenger.send_instrument_off()
    led_manager.transition(POSSIBLE_LED_STATES["IDLE"])
    mainDisplay.set_text_area_value('state', "OFF")


nfcReader = NfcReader(
    on_card_detected = on_card_detected,
    on_card_removed = on_card_removed
)

async def check_nfc_card():
    while True:
        nfcReader.wait_for_card()
        
        await asyncio.sleep(0)

# ##########################################################
# main
#

async def main():
    print('main() running')

    controllerData = ControllerData()

    mainDisplay.set_text_area_value("state", "ON" if controllerData.instrument_on else "OFF")
    mainDisplay.set_text_area_value("fx_1", controllerData.fx1_value)
    mainDisplay.set_text_area_value("fx_1", controllerData.fx2_value)

    rotary_task = asyncio.create_task(rotary_listen(controllerData))
    poll_fx_controls_task = asyncio.create_task(poll_effect_controls(controllerData))
    read_nfc_task = asyncio.create_task(check_nfc_card())
    led_anim_task = asyncio.create_task(run_led_animations())
    midi_listen_task = asyncio.create_task(midi_listen(controllerData))
    blink_beat_task = asyncio.create_task(blink_beat(controllerData))
    
    await asyncio.gather(
        rotary_task,
        poll_fx_controls_task,
        read_nfc_task,
        led_anim_task,
        midi_listen_task,
        blink_beat_task
        )
    
asyncio.run(main())
