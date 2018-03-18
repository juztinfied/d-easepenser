#telegram related imports
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import logging

#tesseract related imports
from PIL import Image
import pytesseract
import cv2
import os
import numpy as np
import requests
import urllib.request

#google drive related imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials


#Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#setting up google sheets access
# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1_YZ3dop4Mxlw5_gcWfuY6n2J6f1EGbCNXOiCA5eoWyk/edit#gid=0')
worksheet = sheet.get_worksheet(0)

#global variables
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract'
BOT_TOKEN = '529982566:AAEhBusHHmFZ6Tq0zVUCg8KBOMgbdh1Z16c'
recipeName = 'empty'
ingredientList = 'empty'

#states
USER_CHOICE, RECIPE_NAME, INPUT_TYPE, CONFIRMATION, BIO = range(5)


def start(bot, update):
    update.message.reply_text("In start function") 
    reply_keyboard = [['Upload Recipe', 'View Recipes']]

    update.message.reply_text(
        'How can I help you?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return USER_CHOICE

def view_recipes(bot,update):
    update.message.reply_text("In view_recipe function")

def recipe_name(bot,update):
    update.message.reply_text("In recipe_name function") 
    bot.send_message(chat_id=update.message.chat_id, text="Name of recipe?")
    return RECIPE_NAME

def enter_recipe_name(bot,update):
    update.message.reply_text("In enter_recipe_name function") 
    recipeName = update.message.text
    logger.info("New recipe name: %s" %recipeName)
    bot.send_message(chat_id=update.message.chat_id, text="Name of recipe: " + recipeName)
    bot.send_message(chat_id=update.message.chat_id, text="Enter ingredient list (text or photo)")
    return INPUT_TYPE

def text_to_text(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text="In text_to_text function")
    ingredientList = update.message.text
    reply_keyboard = [['Yes', 'No']]
    bot.send_message(chat_id=update.message.chat_id, text = 'Ingredient list: ')
    bot.send_message(chat_id=update.message.chat_id, text = ingredientList)
    bot.send_message(chat_id=update.message.chat_id, text = 'Confirm ingredient list?',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CONFIRMATION

def edit_instructions(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text = 'Re-enter ingredient list')
    return INPUT_TYPE

def upload_data(bot,update):
    update.message.reply_text("In upload_instruction function")
    row_search = 2
    filled = worksheet.row_values(row_search)
    while (filled):
        row_search = row_search + 1
        filled = worksheet.row_values(row_search)
    row = [recipeName, ingredientList, recipeInstructions]
        
    
    
    
def image_to_text(bot,update):
    user = update.message.from_user
    update.message.reply_text("in image_to_text function") 
    #fetching photo id from message
    photo_id = update.message.photo[-1].file_id
    logger.info("Photo ID retrieved: %s" %photo_id)
    update.message.reply_text("Photo received. Now processing...")     
    logger.info("Photo received from %s" %user.first_name)
        
    #fetching url with photo's info
    photo_info = ('https://api.telegram.org/bot' + BOT_TOKEN + '/getFile?file_id=' + photo_id)
    logger.info("Photo information retrieved: %s" %photo_info)
       
    #fetching photo's file path 
    photo_file_path = (requests.get(photo_info).json())['result']['file_path']
    logger.info("Photo file path retrieved: %s" %photo_file_path)
    bot.send_message(chat_id=update.message.chat_id, text = "Getting photo info:\n" + photo_file_path)

    #fetching photo's url location
    photo_url = ('https://api.telegram.org/file/bot' + BOT_TOKEN + '/' + photo_file_path)
    logger.info("Photo url retrieved: %s" %photo_url)
        
    #downloading photo in jpg format from photo's url location
    downloaded_photo = urllib.request.urlopen(photo_url)
    logger.info("Photo downloaded in jpg format")
    bot.send_message(chat_id=update.message.chat_id, text = 'Downloading photo in .jpg format...')
        
    #converting to correct format for tesseract
    with open('img.jpg', 'wb') as localFile:
        bot.send_message(chat_id=update.message.chat_id, text = 'Writting the photo into img.jpg...')
        localFile.write(downloaded_photo.read())
        #bot.send_message(chat_id=update.message.chat_id, text = 'Written the photo into img.jpg!')
        #bot.send_message(chat_id=update.message.chat_id, text = 'Using Image.open() on img.jpg...')
        img = Image.open('img.jpg')
        #bot.send_message(chat_id=update.message.chat_id, text = 'Image.open(img.jpg) successful!')
        bot.send_message(chat_id=update.message.chat_id, text = 'Converting image to text')
        tesseract_results = pytesseract.image_to_string(img)
        bot.send_message(chat_id=update.message.chat_id, text = tesseract_results)

    ingredientList = tesseract_results
    reply_keyboard = [['Yes', 'No']]
    bot.send_message(chat_id=update.message.chat_id, text = 'Ingredient list: ')
    bot.send_message(chat_id=update.message.chat_id, text = ingredientList)
    bot.send_message(chat_id=update.message.chat_id, text = 'Confirm ingredient list?',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CONFIRMATION

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            USER_CHOICE: [RegexHandler('^(Upload Recipe)$',
                                       recipe_name),
                          RegexHandler('^View Recipes$',
                                       view_recipes),
                                       ],
            RECIPE_NAME: [MessageHandler(Filters.text, enter_recipe_name)],

            INPUT_TYPE: [MessageHandler(Filters.photo, image_to_text),
                         MessageHandler(Filters.text, text_to_text),
                         ],
            
            CONFIRMATION: [RegexHandler('^(Yes)$',enter_instructions),
                           RegexHandler('^(No)$', edit_instructions),
                           ],

            #LOCATION: [MessageHandler(Filters.location, location),
                       #CommandHandler('skip', skip_location)],

            #BIO: [MessageHandler(Filters.text, bio)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
