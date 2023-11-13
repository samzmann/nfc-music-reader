import asyncio
import board
import digitalio
import keypad

print('code.py running')

is_blinking = True

async def on_button_press(led):
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
                    led.value = 0
            await asyncio.sleep(0)

async def blink(led):
    while True:
        if is_blinking:
            led.value = not led.value
            await asyncio.sleep(1)
        else:
            if led.value:
                led.value = 0
            await asyncio.sleep(0)

async def main():
    print('main() running')

    led = digitalio.DigitalInOut(board.GP25)
    led.switch_to_output()

    button_task = asyncio.create_task(on_button_press(led))
    blink_task = asyncio.create_task(blink(led))
    
    await asyncio.gather(
        button_task,
        blink_task
        )

asyncio.run(main())
