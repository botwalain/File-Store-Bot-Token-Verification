import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
from plugins import web_server
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
from datetime import datetime
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT, FORCESUB_CHANNEL2
from database.db_premium import remove_expired_users
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


# Define the bot class
class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Force Subscription Logic
        if FORCE_SUB_CHANNEL:
            try:
                link = await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                self.invitelink = link
            except Exception as e:
                self.LOGGER(__name__).warning(e)
                self.LOGGER(__name__).info("Bot Stopped. Check FORCE_SUB_CHANNEL configuration.")
                sys.exit()

        if FORCESUB_CHANNEL2:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL2)).invite_link or await self.export_chat_invite_link(FORCESUB_CHANNEL2)
                self.invitelink2 = link
            except Exception as e:
                self.LOGGER(__name__).warning(e)
                self.LOGGER(__name__).info("Bot Stopped. Check FORCESUB_CHANNEL2 configuration.")
                sys.exit()

        # DB Channel Logic
        try:
            self.db_channel = await self.get_chat(CHANNEL_ID)
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).info("Bot Stopped. Check CHANNEL_ID configuration.")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running as @{usr_bot_me.username}!")

        # Start web server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")


# Function to handle scheduled tasks
def schedule_jobs():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(remove_expired_users, "interval", seconds=3600)
    scheduler.start()


# Main entry point
async def main():
    bot = Bot()
    schedule_jobs()
    await bot.start()
    await asyncio.Event().wait()  # Keep the bot running


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
