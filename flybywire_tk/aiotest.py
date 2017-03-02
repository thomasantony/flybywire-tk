import asyncio

async def countdown(ctr=10):
    while ctr >= 0:
        print(ctr)
        await asyncio.sleep(1.0)
        ctr = ctr - 1
    else:
        print('Done')

loop = asyncio.get_event_loop()
loop.run_until_complete(countdown(5.0))
loop.close()
