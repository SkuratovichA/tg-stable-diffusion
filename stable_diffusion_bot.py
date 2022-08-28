#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]
    if __version_info__ < (20, 0, 0, "alpha", 1):
        raise RuntimeError('Install version of telegram newer than 20.0.0.a.1')

import sys
import imagen
import logging
import argparse
from time import sleep
from imagen import Imagen
from telegram.ext import (
    filters,
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
)

from telegram import ForceReply, Update

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(filename)s %(funcName)s() %(levelname)s: %(message)s",
        "%d-%b-%y %H:%M",
    )
)

logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Add arguments
parser = argparse.ArgumentParser()
parser.add_argument('--token', type=str, required=True, help='Telegram Bot token')
parser.add_argument('--test', action='store_true', help='Enabling test mode deactivates qsub command')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    logging.info('*' * 80)
    logging.info(f'User {user["username"]} started a bot\n')
    await update.message.reply_html(
        rf"Hi {user.mention_html()}?"
        "\nI use AI to generate image by a text prompt I receive from you.\n\n"
        "How does it work?."
        "Send me a detailed description of an image you want to generate, wait a bit, and enjoy.\n\n"

        "You can find more information about how to generate beautiful images "
        "<a href=\"https://medium.com/nightcafe-creator/stable-diffusion-tutorial-how-to-use-stable-diffusion-157785632eb3)\">here</a>"
        " (or use a magic tool called google search to find more info by your own)",
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /stop is issued."""
    user = update.effective_user
    logging.info(f'User {user["username"]} stopped a bot\n')
    logging.info('*' * 80)
    await update.message.reply_html(
        rf"Bye.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("https://stability.ai/blog/stable-diffusion-public-release")


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        await update.message.reply_markdown(
            'Ha-ha, funny enough... Hope, the next time, there will be a text provided.'
        )

    logger.info(f'callback query: {update.callback_query}')

    text_prompt = update.message.text

    logger.info('-' * 80)
    logger.info(f'User: {update.effective_user["username"]}')
    logger.info(f'Text prompt: {text_prompt}')

    generator = Imagen(text_prompt)

    message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text='Starting generating the image',
    )

    timeout = generator.get_timout
    for time_elapsed in generator.generate_image():
        await context.bot.edit_message_text(
            text=f"Generating the image...\nTime elapsed: {time_elapsed}/{timeout}s.",
            chat_id=update.message.chat_id,
            message_id=message.message_id
        )

    image_path = generator.get_image_path
    if not image_path:
        await context.bot.edit_message_text(
            text=f"Unable to generate the image",
            chat_id=update.message.chat_id,
            message_id=message.message_id
        )
    else:
        await update.message.reply_photo(photo=open(image_path, 'rb'), caption='`'+text_prompt+'`')


def main(token) -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(token)
        .arbitrary_callback_data(True)
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    # application.add_handler(CallbackQueryHandler())
    logger.info('Running a bot...')
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    args = parser.parse_args()
    imagen.set_generating_enabled(not args.test)

    main(args.token)
