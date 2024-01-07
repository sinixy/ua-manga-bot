import asyncio


async def run():
    from bot import bot, Bot, dp
    from bot.scheduler import scheduler
    scheduler.ctx.add_instance(bot, Bot)    

    scheduler.start()
    print('JOBS LOADED:', len(scheduler.get_jobs()))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())