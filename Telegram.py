import logging
from VideoLookup import searchDepartments, searchLectures

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import json
import re
import Subscriptions
from threading import Event
from time import time
from datetime import timedelta
import threading

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

lock = threading.RLock()

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
	"""Send a message when the command /start is issued."""
	keyboard = [[InlineKeyboardButton("Subscribe", callback_data='1'),
				 InlineKeyboardButton("Unsubscribe", callback_data='2')]]

	reply_markup = InlineKeyboardMarkup(keyboard)
	update.message.reply_text('Hello! What would you like to do?', reply_markup=reply_markup)

def help(update, context):
	"""Send a message when the command /help is issued."""
	update.message.reply_text('Hello! This bot can send you updates when new videos are uploaded to the ETH-Videothek.')

def button(update, context):
	lock.acquire()
	query = update.callback_query

	if query.data == "0":
		cancel(update, context)
	elif query.data == "1":
		subscribe(update, context)
	elif query.data == "2":
		unsubscribe(update, context)
	elif query.data == "3":
		nightline(update, context)
	else: 
		data = json.loads(query.data)
		if not "L" in data:
			error(update, context)
		elif data["L"] == 1:
			departmentSelect(update, context)
		elif data["L"] == 2:
			lectureSelect(update, context)
		elif data["L"] == 3:
			confirm(update, context)
	
	lock.release()

def subscribe(update, context):
	keyboard = []
	departmentList = searchDepartments()
	for department in departmentList:
		keyboard.append([InlineKeyboardButton(department, callback_data=json.dumps({"L": 1, "S": 1, "D": department}))])

	query = update.callback_query
	reply_markup = InlineKeyboardMarkup(keyboard)
	query.edit_message_text(text='Which department does your lecture belong to?', reply_markup=reply_markup)

def unsubscribe(update, context):
	keyboard = []
	departmentList = searchDepartments()
	for department in departmentList:

		keyboard.append([InlineKeyboardButton(department, callback_data=json.dumps({"L": 1, "S": 0, "D": department}))])

	query = update.callback_query
	reply_markup = InlineKeyboardMarkup(keyboard)
	query.edit_message_text(text='Which department does your lecture basedlong to?', reply_markup=reply_markup)

def nightline(update, context):
	query = update.callback_query
	query.edit_message_text(text='www.nightline.ch')

def departmentSelect(update, context):
	query = update.callback_query
	keyboard = []
	data = json.loads(query.data)
	data['L'] = 2

	if re.match("^D-[A-Z][A-Z][A-Z][A-Z]$", data["D"]):
		lectureList = searchLectures(data["D"])
		i = 0
		for lecture in lectureList:
			data['V'] = i
			keyboard.append([InlineKeyboardButton(lecture["Name"], callback_data=json.dumps(data))])
			i += 1

		reply_markup = InlineKeyboardMarkup(keyboard)
		query.edit_message_text(text='Which lecture are you interested in?', reply_markup=reply_markup)
	else:
		error(update, context)

def lectureSelect(update, context):
	query = update.callback_query

	data = json.loads(query.data)
	data['L'] = 3

	if re.match("^D-[A-Z][A-Z][A-Z][A-Z]$", data["D"]):
		lectureList = searchLectures(data["D"])
		lecture = lectureList[data['V']]

		data['C'] = 1
		keyboard = [[InlineKeyboardButton("Yes", callback_data=json.dumps(data)),
				 InlineKeyboardButton("No", callback_data="0")]]

		reply_markup = InlineKeyboardMarkup(keyboard)
		query.edit_message_text(text='Are you interested in ' + lecture["Name"] + ": " + lecture["Link"][50-21:-5] + "?", reply_markup=reply_markup)
	else:
		error(update, context)

def confirm(update, context):
	query = update.callback_query

	data = json.loads(query.data)

	if re.match("^D-[A-Z][A-Z][A-Z][A-Z]$", data["D"]):
		lectureList = searchLectures(data["D"])
		lecture = lectureList[data['V']]

		Subscriptions.process(lecture['Link'], update['callback_query']['message']['chat']['id'], data["S"])

		query.edit_message_text(text='Alright! Type /start to find more lectures!')
	else:
		error(update, context)

def cancel(update, context):
	query = update.callback_query
	query.edit_message_text(text='Okay! Type /start to restart!')   

def error(update, context):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def checkForUpdates(context):
	changes = Subscriptions.checkChanges()

	for i in range(0, len(changes)):
		for j in range(0, len(changes[i][0])):
			content = "A new video has been posted in \"" + str(changes[i][1][1]) + "\" on the " + str(changes[i][1][2]) + " : " + "https://video.ethz.ch" + str(changes[i][1][0])
			context.bot.send_message(chat_id=changes[i][0][j], text=content)

def main():
	"""Start the bot."""
	# Create the Updater and pass it your bot's token.
	# Make sure to set use_context=True to use the new context based callbacks
	# Post version 12 this will no longer be necessary
	token = open("token", "r").read()
	Subscriptions.load()
	updater = Updater(token, use_context=True)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", help))

	# on noncommand i.e message - echo the message on Telegram

	updater.dispatcher.add_handler(CallbackQueryHandler(button))

	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	updater.start_polling()

	job_queue = updater.job_queue

    # Periodically save jobs

	job_queue.run_repeating(checkForUpdates, timedelta(seconds=10*60))
	

	# Run the bot until you press Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	main()
