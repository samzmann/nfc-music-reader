import asyncio
import board
import digitalio
from analogio import AnalogIn
import keypad
import busio
import displayio
import terminalio
import countio
import time
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_display_text import label
from rotary_encoder import RotaryEncoder
from adafruit_pn532.i2c import PN532_I2C

# ##########################################################
# ControllerData
#

class ControllerData():
    def __init__(self, initial_interval, onChangeValue, onChangeMode, onChangePotValue):
        self.mode = "PLAY"
        self.value = initial_interval
        self.pot_value = 0
        self.onChangeValue = onChangeValue
        self.onChangeMode = onChangeMode
        self.onChangePotValue = onChangePotValue
        self.counter = countio.Counter(board.GP17)
        self.last_card_timestamp = time.monotonic()
        self.last_card_id = None

    def changeValue(self, increment):
        print('changeValue', increment)
        if increment:
            self.value += 1
        else: 
            self.value -= 1
        self.onChangeValue(self.value)

    def changeMode(self):
        if self.mode == "PLAY":
            self.mode = "WRITE"
        else:
            self.mode = "PLAY"
        self.onChangeMode(self.mode)

    def changePotValue(self, potValue):
        if potValue != self.pot_value:
            self.pot_value = potValue
            self.onChangePotValue(self.pot_value)


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
# Potentiometer
#

async def pot_listen(potentiometer: AnalogIn, controllerData: ControllerData):        
    while True:
        pot_val = potentiometer.value
        controllerData.changePotValue(pot_val)

        await asyncio.sleep(0.2)

# ##########################################################
# Display
#

def init_display():
    displayio.release_displays()

    screen_width = 128
    screen_height = 64

    i2c_1 = busio.I2C(board.GP7, board.GP6)
    display_bus = displayio.I2CDisplay(i2c_1, device_address=0x3C)
    display = SSD1306(display_bus, width=screen_width, height=screen_height)
    display.root_group.hidden = True

    # Make the display context
    splash = displayio.Group()
    display.show(splash)

    value_text_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=5)
    value_text_area.text = f"Value: {0}"
    splash.append(value_text_area)

    mode_text_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=20)
    mode_text_area.text = f"Mode: PLAY"
    splash.append(mode_text_area)

    pot_text_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=35)
    pot_text_area.text = f"Pot: 0"
    splash.append(pot_text_area)

    return (value_text_area, mode_text_area, pot_text_area)


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

    (value_text_area, mode_text_area, pot_text_area) = init_display()

    potentiometer = AnalogIn(board.GP28)

    led = digitalio.DigitalInOut(board.GP25)
    led.switch_to_output()

    def writeControllerValue(v):
        value_text_area.text = f"Value: {v}"

    def writeControllerMode(m):
            mode_text_area.text = f"Mode: {m}"

    def writeControllerPotValue(v):
            pot_text_area.text = f"Pot: {v}"

    controllerData = ControllerData(0, writeControllerValue, writeControllerMode, writeControllerPotValue)


    button_task = asyncio.create_task(on_button_press(led, controllerData))
    blink_task = asyncio.create_task(blink(led))
    rotary_task = asyncio.create_task(rotary_listen(controllerData))
    potentiometer_task = asyncio.create_task(pot_listen(potentiometer, controllerData))
    interrupt_task = asyncio.create_task(catch_interrupt(controllerData, led))
    
    await asyncio.gather(
        button_task,
        blink_task,
        rotary_task,
        potentiometer_task,
        interrupt_task
        )
    

asyncio.run(main())
