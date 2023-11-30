import asyncio
from led_manager import LedManager

leds = LedManager()

async def change_leds():
    state_index = 0
    while True:
        await asyncio.sleep(5)
        
        state_index += 1
        if state_index == len(leds.possible_states):
            state_index = 0

        leds.transition(leds.possible_states[state_index])

        await asyncio.sleep(0)


async def run_anim():
    while True:
        leds.animate()
        await asyncio.sleep(0)


async def main():
    print('main() running')

    change_state_task = asyncio.create_task(change_leds())
    anim_task = asyncio.create_task(run_anim())

    await asyncio.gather(
        change_state_task,
        anim_task
    )


asyncio.run(main())
    
