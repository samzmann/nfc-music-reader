import asyncio
import board
import digitalio
import keypad
import busio
import countio
import time
from adafruit_pn532.i2c import PN532_I2C

from effect_control import EffectControl
from rotary_encoder import RotaryEncoder
from main_display import MainDisplay

# ##########################################################
# ControllerData
#

class ControllerData():
    def __init__(self, initial_interval, on_updt_mode, on_updt_fx_1, on_updt_fx_2):
        self.mode = "PLAY"
        self.value = initial_interval
        self.pot_value = 0
        self.on_updt_mode = on_updt_mode
        self.on_updt_fx_1 = on_updt_fx_1
        self.on_updt_fx_2 = on_updt_fx_2
        self.counter = countio.Counter(board.GP17)
        self.last_card_timestamp = time.monotonic()
        self.last_card_id = None

    def changeValue(self, increment):
        print('changeValue', increment)
        if increment:
            self.value += 1
        else: 
            self.value -= 1
        self.on_updt_fx_2(self.value)

    def changeMode(self):
        if self.mode == "PLAY":
            self.mode = "WRITE"
        else:
            self.mode = "PLAY"
        self.on_updt_mode(self.mode)

    def changePotValue(self, potValue):
        if potValue != self.pot_value:
            self.pot_value = potValue
            self.on_updt_fx_1(self.pot_value)


# ##########################################################
# Rotary Encoder
#

rotaryEncoder = RotaryEncoder(
    board.GP13,
    board.GP14
)

async def rotary_listen(controllerData: ControllerData):        
    while True:
        rotaryEncoder.listenToRotation(controllerData.changeValue)
        await asyncio.sleep(0)

# ##########################################################
# Effect controls (potentiometers and other analog input devices)
#

async def poll_effect_controls(effect_controls, controllerData: ControllerData):
    while True:
        for fx_device in effect_controls:
            fx1_val = fx_device.get_value()
            controllerData.changePotValue(fx1_val)
        await asyncio.sleep(0.2)

# ##########################################################
# Display
#

mainDisplay = MainDisplay()

# ##########################################################
# Blink
#

is_blinking = True

async def on_button_press(led, controllerData: ControllerData):
    global is_blinking

    with keypad.Keys(
        (board.GP15,), value_when_pressed=False, pull=True
    ) as keys:
        while True:
            key_event = keys.events.get()
            if key_event:
                if key_event.pressed:
                    print("button pressed")
                    is_blinking = not is_blinking
                    led.value = 1
                    controllerData.changeMode()

            await asyncio.sleep(0)

async def blink(led):
    while True:
        if is_blinking:
            led.value = not led.value
            await asyncio.sleep(1)
        else:
            if not led.value:
                led.value = 1
            await asyncio.sleep(0)

# ##########################################################
# NFC
#

i2c_0 = busio.I2C(board.GP5, board.GP4)

pn532 = PN532_I2C(
    i2c_0, 
    debug=False,
    irq=board.GP17
    )

pn532.SAM_configuration()

pn532.listen_for_passive_target()

async def catch_interrupt(controllerData: ControllerData, led):
    global is_blinking

    while True:
        if controllerData.counter.count > 0:
            print('must read card', controllerData.counter.count)
            uid = pn532.get_passive_target()
            cardIdString = None
            if uid is not None:
                print("UID:", ''.join(hex(i) for i in uid))
                cardIdString = ''.join(hex(i) for i in uid)
                controllerData.last_card_id = cardIdString
            pn532.listen_for_passive_target()
            controllerData.counter.reset()
            controllerData.last_card_timestamp = time.monotonic()
            led.value = 1
            is_blinking = False
        elif time.monotonic() > controllerData.last_card_timestamp + 0.5 and not is_blinking:
            is_blinking = True
            print(f'card {controllerData.last_card_id} lost')
            controllerData.last_card_id = None
            
        await asyncio.sleep(0)

# ##########################################################
# main
#

async def main():
    print('main() running')

    fx1 = EffectControl(board.GP28, 200, 65000)

    all_fx = [
        fx1
    ]

    led = digitalio.DigitalInOut(board.GP25)
    led.switch_to_output()

    def updt_mode_display(m):
            mainDisplay.set_text_area_value('mode', m)

    def updt_fx_1_display(v):
            mainDisplay.set_text_area_value('fx_1', v)

    def updt_fx_2_display(v):
        mainDisplay.set_text_area_value('fx_2', v)

    controllerData = ControllerData(
        0,
        updt_mode_display,
        updt_fx_1_display,
        updt_fx_2_display,
        )

    button_task = asyncio.create_task(on_button_press(led, controllerData))
    blink_task = asyncio.create_task(blink(led))
    rotary_task = asyncio.create_task(rotary_listen(controllerData))
    poll_fx_controls_task = asyncio.create_task(poll_effect_controls(all_fx, controllerData))
    interrupt_task = asyncio.create_task(catch_interrupt(controllerData, led))
    
    await asyncio.gather(
        button_task,
        blink_task,
        rotary_task,
        poll_fx_controls_task,
        interrupt_task
        )
    

asyncio.run(main())
