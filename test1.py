
import asyncio


async def print_number(n):
    print(n)
    await asyncio.sleep(0.5)


async def spawn():
    print('alive')
    await asyncio.sleep(1)
    asyncio.ensure_future(print_number(1))
    asyncio.ensure_future(print_number(2))


asyncio.ensure_future(spawn())
asyncio.get_event_loop().run_forever()