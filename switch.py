import board
import digitalio
from adafruit_debouncer import Debouncer
import time

ON = "ON"
OFF = "OFF"
BLINK = "BLINK"

BLINK_DURATION_S = 0.5


class Switch:

    blinkTimestamp = 0
    prevBlinkState = False

    def __init__(self, buttonPin, ledPin, onCLick, state=ON) -> None:
        pin_input = digitalio.DigitalInOut(buttonPin)
        pin_input.switch_to_input(pull=digitalio.Pull.UP)
        self.switch = Debouncer(pin_input)

        self.led = digitalio.DigitalInOut(ledPin)
        self.led.direction = digitalio.Direction.OUTPUT

        self.onCLick = onCLick

        self.setState(state)

    def setState(self, state):

        self.state = state

        if self.state == ON:
            self.led.value = 1

        if self.state == OFF:
            self.led.value = 0

        if self.state == BLINK:
            self.blinkTimestamp = time.monotonic()
            self.prevBlinkState = 1
            self.led.value = 1

        print("setState", state, self.state)

    def animateBlink(self):

        now = time.monotonic()

        if now > self.blinkTimestamp + BLINK_DURATION_S:
            print("blink", now)
            self.blinkTimestamp = now
            self.prevBlinkState = not self.prevBlinkState
            self.led.value = self.prevBlinkState

    def update(self):
        self.switch.update()
        if self.switch.fell:
            print("Just pressed")
            self.onCLick()

        if self.switch.rose:
            print("switch.rose")


        if self.state == BLINK:
            self.animateBlink()
