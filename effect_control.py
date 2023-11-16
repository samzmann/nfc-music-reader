from microcontroller import Pin
from analogio import AnalogIn

class EffectControl():
    def __init__(self, pin: Pin, value_min: float, value_max: float) -> None:
        self.input_device = AnalogIn(pin)
        self.value_min = value_min
        self.value_max = value_max

    def get_value(self):
        return self.input_device.value