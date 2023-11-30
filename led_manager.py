import board, neopixel

from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.rainbowchase import RainbowChase

from adafruit_led_animation.sequence import AnimationSequence

from adafruit_led_animation.color import AMBER, PURPLE

POSSIBLE_LED_STATES = {
    "IDLE": "IDLE",
    "TRANSITION": "TRANSITION",
    "LIVE": "LIVE"
}


class LedManager():
    possible_states = [
        "IDLE",
        "TRANSITION",
        "LIVE"
    ]
    state = "IDLE"

    def __init__(self) -> None:
        self.pixel_pin = board.GP16
        self.num_pixels = 10

        self.pixels = neopixel.NeoPixel(
            self.pixel_pin,
            self.num_pixels,
            brightness=0.2,
            auto_write=False,
            pixel_order=neopixel.GRB
        )

        self.pulse = Pulse(self.pixels, speed=0.05, color=AMBER, period=2)
        self.comet_down = Comet(self.pixels, speed=0.5 / self.num_pixels, color=PURPLE, tail_length=5, bounce=False)
        self.comet_up = Comet(self.pixels, speed=0.5 / self.num_pixels, color=PURPLE, tail_length=5, bounce=False, reverse=True)
        self.rainbow_chase = RainbowChase(self.pixels, speed=0.1, size=5, spacing=3)

        self.animation_seq = AnimationSequence(
            self.pulse,
            self.comet_down,
            self.comet_up,
            auto_clear=True, auto_reset=True, advance_on_cycle_complete=True)
        
        self.anim_idle = self.pulse
        self.anim_transition = self.animation_seq
        self.anim_live = self.rainbow_chase

        self.anim_for_state = self.anim_idle

    def animate(self):
        self.anim_for_state.animate()
    
    def transition(self, to_sate: str):
        self.state = to_sate
        self.anim_for_state.reset()

        print('change state to', to_sate)

        if self.state is POSSIBLE_LED_STATES["IDLE"]:
            self.anim_for_state = self.anim_idle
        elif self.state is POSSIBLE_LED_STATES["TRANSITION"]:
            self.anim_for_state = self.anim_transition
        elif self.state is POSSIBLE_LED_STATES["LIVE"]:
            self.anim_for_state = self.anim_live



    
    
