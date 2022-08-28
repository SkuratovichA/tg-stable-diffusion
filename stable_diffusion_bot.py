#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

import logging
import string
import random
from telegram import __version__ as TG_VER
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError('pizda dolbaeb')
from telegram import ForceReply, Update
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters

# Enable logging

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


from imagen import Imagen

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logging.info("Strting a bot")

    await update.message.reply_text(
        f"Hi {user.mention_markdown()}\n"
        "stable diffusion description & options ?lalala"
         )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /stop is issued."""
    user = update.effective_user
    logging.info("Stopping a bot")
    await update.message.reply_html(
        rf"Bye.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("https://stability.ai/blog/stable-diffusion-public-release")


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        await update.message.reply_markdown('Ha-ha, funny enough... Hope, the next time, there will be a text provided.')

    text_prompt = update.message.text
    generator  = Imagen(text_prompt)

    logger.info('-' * 80)
    logger.info(f'User: {update.effective_user}')
    logger.info(f'Text prompt: ')
    logger.info(f'Text prompt: ')

    query = update.callback_query
    image_path = generator.generate_image()


    if image_path is None:
        await update.message.reply_markdown('Well, something bad happened while photo have been generated. Hence, you read this text. ((really sorry))')
    else:
        await update.message.reply_photo(photo=open(image_path, 'rb'), caption=text_prompt)



def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    token = '5479486611:AAHmQ0jOtyjdjFW9fWo2hqQGzsoc_-Wd3iU'
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(CommandHandler("generate", generate_image))

    # on non command i.e message - summarize a message using huggingface transformer
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    logger.info('Running a bot')
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

