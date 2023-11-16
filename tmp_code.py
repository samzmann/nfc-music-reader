from adafruit_pn532.i2c import PN532_I2C
import countio
import asyncio
import busio
import board

class ControllerData():
    def __init__(self):
        self.counter = countio.Counter(board.GP17)

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

async def catch_interrupt(controllerData: ControllerData):
    while True:
        if controllerData.counter.count == 1:
            print('must read card', controllerData.counter.count)
            uid = pn532.get_passive_target()
            if uid is not None:
                print("UID:", [hex(i) for i in uid])
            pn532.listen_for_passive_target()
            controllerData.counter.count = 0
        await asyncio.sleep(0)

async def main():
    controllerData = ControllerData()
    interrupt_task = asyncio.create_task(catch_interrupt(controllerData))

    await asyncio.gather(interrupt_task)

asyncio.run(main())
