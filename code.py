import asyncio
import board
import digitalio
import keypad
from adafruit_simplemath import map_range

from effect_control import EffectControl
from rotary_encoder import RotaryEncoder
from main_display import MainDisplay
from led_manager import LedManager, POSSIBLE_LED_STATES
from nfc_reader import NfcReader
from midi_messenger import MidiMessenger

# ##########################################################
# MIDI
#

midi_messenger = MidiMessenger()

# ##########################################################
# Display
#

mainDisplay = MainDisplay()

# ##########################################################
# ControllerData
#

class ControllerData():
    def __init__(self):

        self.instrument_on = False
        self.fx1_value = 100
        self.fx2_value = 100


# ##########################################################
# Rotary Encoder
#

rotaryEncoder = RotaryEncoder(
    board.GP13,
    board.GP14
)

async def rotary_listen(controllerData: ControllerData):        
    while True:
        direction = rotaryEncoder.listenToRotation()
        
        if direction is not None:
            print('on_rotate', direction)
            if direction == "CLOCKWISE":
                controllerData.fx1_value = min(127, controllerData.fx1_value + 1)
            elif direction == "ANTICLOCKWISE":
                controllerData.fx1_value = max(0, controllerData.fx1_value - 1)
            midi_messenger.send_instrument_fx1(controllerData.fx1_value)
            mainDisplay.set_text_area_value('fx_1', controllerData.fx1_value)
            print('state.fx_val', controllerData.fx1_value)  
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
        await asyncio.sleep(0.2)

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
    print('change to live')
    led_manager.transition(POSSIBLE_LED_STATES["LIVE"])
    midi_messenger.send_instrument_on()

def on_card_removed():
    print('change to idle')
    led_manager.transition(POSSIBLE_LED_STATES["IDLE"])
    midi_messenger.send_instrument_off()


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

    rotary_task = asyncio.create_task(rotary_listen(controllerData))
    poll_fx_controls_task = asyncio.create_task(poll_effect_controls(controllerData))
    read_nfc_task = asyncio.create_task(check_nfc_card())
    led_anim_task = asyncio.create_task(run_led_animations())
    
    await asyncio.gather(
        rotary_task,
        poll_fx_controls_task,
        read_nfc_task,
        led_anim_task
        )
    
asyncio.run(main())
