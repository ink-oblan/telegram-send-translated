from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from . import handlers
from .config import load_config
from .providers import build_registry
from .storage import Storage


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()

    storage = Storage(config.db_path)
    await storage.connect()
    registry = build_registry(config)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(handlers.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(
            bot,
            registry=registry,
            storage=storage,
            config=config,
        )
    finally:
        await registry.aclose()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
