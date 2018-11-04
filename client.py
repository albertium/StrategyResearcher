
import asyncio
import logging
import random
import string
import uuid

import attr


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
)


@attr.s
class PubSubMessage:
    instance_name = attr.ib()
    msg_id = attr.ib(repr=False)
    hostname = attr.ib(repr=False, init=False)

    def __attrs_post_init__(self):
        self.hostname = f'{self.instance_name}.example.net'


# simulating an external publisher of events
async def publish(queue):
    choices = string.ascii_lowercase + string.digits
    while True:
        msg_id = str(uuid.uuid4())
        host_id = ''.join(random.choices(choices, k=4))
        instance_name = f'cattle-{host_id}'
        msg = PubSubMessage(msg_id=msg_id, instance_name=instance_name)
        # put the item in the queue
        await queue.put(msg)
        logging.info(f'Published message {msg}')

        # simulate randomness of publishing messages
        await asyncio.sleep(random.random())


async def restart_host(msg):
    # unhelpful simulation of i/o work
    await asyncio.sleep(random.random())
    logging.info(f'Restarted {msg.hostname}')


async def consume(queue):
    while True:
        msg = await queue.get()
        logging.info(f'Pulled {msg}')

        asyncio.ensure_future(restart_host(msg))


async def handle_exception(coro, loop):
    try:
        await coro
    except Exception:
        logging.error('Caught exception')
        loop.stop()


if __name__ == '__main__':
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    publisher_coro = handle_exception(publish(queue), loop)
    consumer_coro = handle_exception(consume(queue), loop)

    try:
        loop.create_task(publisher_coro)
        loop.create_task(consumer_coro)
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('Interrupted')
    finally:
        logging.info('Cleaning up')
        loop.stop()