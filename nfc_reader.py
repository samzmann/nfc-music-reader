import board
import busio
import countio
import time
from adafruit_pn532.i2c import PN532_I2C

class NfcReader():
    def __init__(self):
        i2c_0 = busio.I2C(board.GP5, board.GP4)

        self.pn532 = PN532_I2C(
            i2c_0, 
            debug=False,
            irq=board.GP17
            )
        self.interrupt = countio.Counter(board.GP17)
        
        self.pn532.SAM_configuration()
        self.pn532.listen_for_passive_target()

        self.last_card_id = None
        self.last_card_timestamp = time.monotonic()

    def wait_for_card(self):
        if self.interrupt.count > 0:
            print('must read card', self.interrupt.count)
            uid = self.pn532.get_passive_target()
            cardIdString = None
            if uid is not None:
                print("UID:", ''.join(hex(i) for i in uid))
                cardIdString = ''.join(hex(i) for i in uid)
                self.last_card_id = cardIdString
            self.pn532.listen_for_passive_target()
            self.interrupt.reset()
            self.last_card_timestamp = time.monotonic()
        elif time.monotonic() > self.last_card_timestamp + 0.5 and self.last_card_id is not None:
            print(f'card {self.last_card_id} lost')
            self.last_card_id = None