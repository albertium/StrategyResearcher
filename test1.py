
import asyncio
import threading
import queue
import time


loop = asyncio.get_event_loop()
# q = asyncio.Queue()
q = queue.Queue()
event = threading.Event()


async def printing():
    while True:
        # msg = await q.get()
        msg = q.get()
        event.set()
        print(msg)

        if msg == 'closed':
            break

    loop.stop()


def runner():
    loop.run_forever()
    print('we r done')


asyncio.run_coroutine_threadsafe(printing(), loop)
t = threading.Thread(target=runner)
t.start()

for i in range(5):
    # queue.put_nowait(i)
    q.put(i)
q.put_nowait('closed')

t.join()
print(event.is_set())
# print('finished')

