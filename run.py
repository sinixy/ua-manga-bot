import asyncio


async def run():
    from bot import bot, Bot, dp
    from bot.scheduler import scheduler
    scheduler.ctx.add_instance(bot, Bot)    

    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())