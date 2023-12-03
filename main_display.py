import displayio
import busio
import board
import terminalio
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_display_text import label

class MainDisplay():
    def __init__(self):
        displayio.release_displays()

        screen_width = 128
        screen_height = 64

        i2c_1 = busio.I2C(board.GP7, board.GP6)
        display_bus = displayio.I2CDisplay(i2c_1, device_address=0x3C)
        display = SSD1306(display_bus, width=screen_width, height=screen_height)

        # This is necessary to avoid debug messages being showin on the display.
        display.root_group.hidden = True

        # Make the display context
        splash = displayio.Group()
        display.show(splash)

        self.state_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=5)
        self.state_area.text = "State: ---"
        splash.append(self.state_area)

        self.fx_1_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=20)
        self.fx_1_area.text = "FX 1: ---"
        splash.append(self.fx_1_area)

        self.fx_2_area = label.Label(terminalio.FONT, text=" "*21, x=0, y=35)
        self.fx_2_area.text = "FX 2: ---"
        splash.append(self.fx_2_area)

    def set_text_area_value(self, area, value):
        if area == "state":
            self.state_area.text = f"State: {value}"
        if area == "fx_1":
            self.fx_1_area.text = f"FX 1: {value}"
        if area == "fx_2":
            self.fx_2_area.text = f"FX 2: {value}"