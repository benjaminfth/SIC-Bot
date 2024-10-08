from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import logging
from aiohttp import web
import threading
from p1 import assemble
import os

Token = os.environ.get("TOKEN", "")
BOT_USERNAME = 'sicassemblerbot'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

INPUT, OPTAB = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    firstname = update.message.from_user.first_name
    logger.info("Starting conversation: asking for input code")
    await update.message.reply_text(f"Hi {firstname}! Welcome to the SIC Assembler bot! \n\nEnter Input Code to Assemble")
    return INPUT

async def input_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input_code = update.message.text
    context.user_data['input_code'] = user_input_code
    logger.info(f"Received input code: {user_input_code}")
    await update.message.reply_text("Enter Optab")
    return OPTAB

async def optab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_optab = update.message.text
    context.user_data['optab'] = user_optab
    logger.info(f"Received optab: {user_optab}")

    input_code = context.user_data['input_code']
    optab = context.user_data['optab']

    intermediate_output, symtab_output, output_text, object_output = assemble(input_code, optab)

    if intermediate_output is None:
        await update.message.reply_text(f"Error: {symtab_output}")
    else:
        await update.message.reply_text(
            f"Intermediate Output:\n{intermediate_output}\n\n"
            f"Symtab Output:\n{symtab_output}\n\n"
            f"Final Output:\n{output_text}\n\n"
            f"Object Code:\n{object_output}"
        )

    return ConversationHandler.END

async def About(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Welcome to the SIC Assembler bot!")

if __name__ == '__main__':
    application = ApplicationBuilder().token(Token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_code)],
            OPTAB: [MessageHandler(filters.TEXT & ~filters.COMMAND, optab)],
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: (
            update.message.reply_text("Conversation cancelled."),
            ConversationHandler.END
        ))],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))

    # Run the bot polling in a separate thread
    def run_bot():
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    threading.Thread(target=run_bot).start()

    # Run the web server in the main thread
    app = web.Application()
    web.run_app(app, port=8000)