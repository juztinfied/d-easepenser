#telegram related imports
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import logging

#testing zi jun
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
#BOT_TOKEN = '476170496:AAEp4-B-N96lVb4GZOhhREjNhVIs9x0hpbo' #for tin_bot
BOT_TOKEN = '529982566:AAEhBusHHmFZ6Tq0zVUCg8KBOMgbdh1Z16c' #for deasepenser
recipeName = 'empty'
ingredientList = 'empty'
recipeInstructions = 'empty'
confirm_vector = {'rname': False, 'ingredientList': False, 'recipeInstructions': False}

#states
USER_CHOICE, RECIPE_NAME, INPUT_TYPE, CONFIRMATION, MAINMENU = range(5)


def start(bot, update):
    update.message.reply_text("In start function") 
    reply_keyboard = [['Upload Recipe', 'View Recipes'],['BAKE']]

    update.message.reply_text(
        'How can I help you?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return USER_CHOICE

def view_recipes(bot,update):
    update.message.reply_text("In view_recipe function")

def enter_recipe_name(bot,update):
    update.message.reply_text("In recipe_name function") 
    bot.send_message(chat_id=update.message.chat_id, text="Name of recipe?")
    return RECIPE_NAME

def enter_ingredients(bot,update):
    global recipeName
    update.message.reply_text("In enter_recipe_name function") 
    recipeName = update.message.text
    logger.info("New recipe name: %s" %recipeName)
    confirm_vector['rname'] = True
    bot.send_message(chat_id=update.message.chat_id, text="Name of recipe: " + recipeName)
    bot.send_message(chat_id=update.message.chat_id, text="Enter ingredient list (text or photo)")
    return INPUT_TYPE

def text_to_text(bot,update):
    global ingredientList
    global recipeInstructions
    
    bot.send_message(chat_id=update.message.chat_id, text="In text_to_text function")
    reply_keyboard = [['Yes', 'No']]
    
    if (ingredientList == 'empty' or confirm_vector['ingredientList'] == False): #if ingredientList not filled yet or not confirmed yet
        ingredientList = update.message.text #fill up ingredientList with user input
        bot.send_message(chat_id=update.message.chat_id, text = 'Ingredient list: ')
        bot.send_message(chat_id=update.message.chat_id, text = ingredientList)
        bot.send_message(chat_id=update.message.chat_id,
                         text = 'Confirm ingredient list?',
                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                         )
    
    elif (recipeInstructions == 'empty' or confirm_vector['recipeInstructions'] == False): #if recipeInstructions not filled yet or not confirmed
        recipeInstructions = update.message.text
        bot.send_message(chat_id=update.message.chat_id, text = 'Recipe Instructions: ')
        bot.send_message(chat_id=update.message.chat_id, text = recipeInstructions)
        bot.send_message(chat_id=update.message.chat_id,
                         text = 'Confirm recipe instructions?',
                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                         )
        
    return CONFIRMATION

def image_to_text(bot,update):
    global recipeInstructions
    global ingredientList
    
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

    if (confirm_vector['ingredientList'] == False): #if ingredientList not confirmed yet
        ingredientList = update.message.text #fill up ingredientList
        bot.send_message(chat_id=update.message.chat_id, text = 'Ingredient list: ')
        bot.send_message(chat_id=update.message.chat_id, text = ingredientList)
        bot.send_message(chat_id=update.message.chat_id,
                         text = 'Confirm ingredient list?',
                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                         )
    
    elif (confirm_vector['recipeInstructions'] == False): #if recipeInstructions not filled yet
        recipeInstructions = update.message.text
        bot.send_message(chat_id=update.message.chat_id, text = 'Recipe Instructions: ')
        bot.send_message(chat_id=update.message.chat_id, text = recipeInstructions)
        bot.send_message(chat_id=update.message.chat_id,
                         text = 'Confirm recipe instructions?',
                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                         )

    return CONFIRMATION

def edit_entry(bot,update):
    if (confirm_vector['ingredientList'] == False): #if user have not confirm ingredient list
        bot.send_message(chat_id=update.message.chat_id, text = 'Re-enter ingredient list')
    
    elif (confirm_vector['recipeInstructions'] == False): #if user entered instructions but haven confirm it yet
        bot.send_message(chat_id=update.message.chat_id, text = 'Re-enter recipe instructions')
        
    return INPUT_TYPE

def enter_instructions(bot,update):
    global ingredientList
    global recipeInstructions
    global confirm_vector

    bot.send_message(chat_id=update.message.chat_id, text = 'In enter_instructions function')
    
    if (ingredientList != 'empty'): #if user has filled in ingredientList and he is in this loop, means he confirmed the ingredientList already
        confirm_vector['ingredientList'] = True #confirm ingredientList in the vector

    if (recipeInstructions == 'empty'): #if user has not ever entered recipe instructions before
        bot.send_message(chat_id=update.message.chat_id, text = 'Enter recipe instructions')
        return CONFIRMATION
        #will be send to text_to_text or image_to_text, after that user will reply with YES or NO
        #if user reply with YES, goto enter_instructions
        #if user reply with NO, go to edit_entry, then go to text_to_text or image_to_text

    elif (recipeInstructions != 'empty'): #if it is not empty and user is here, means that he has confirmed the instructions
        confirm_vector['recipeInstruction'] = True 
        upload_data(bot,update)
        return ConversationHandler.END

    else:
        bot.send_message(chat_id=update.message.chat_id, text = 'Something is wrong somewhere...')
        return ConversationHandler.END
        

def upload_data(bot,update):
    update.message.reply_text("In upload_data function")
    row_to_fill = 2
    filled = worksheet.row_values(row_to_fill)
    while (filled):
        row_to_fill = row_to_fill + 1
        filled = worksheet.row_values(row_to_fill)
        
    rowData = [recipeName, ingredientList, recipeInstructions]
    worksheet.insert_row(rowData,row_to_fill)
    bot.send_message(chat_id=update.message.chat_id, text =
                     'New recipe has been uploaded:\n'+
                     'Recipe Name:'+rowData[0]+'\n'+
                     'Ingredient List:'+rowData[1]+'\n'+
                     'Instructions:'+rowData[2]
                    )
    
    reply_keyboard = [['Terminate', 'Main Menu']]
    bot.send_message(chat_id=update.message.chat_id, text = 'Where do you want to go now?',
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                     )
    return MAINMENU

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the sequence", user.first_name)
    update.message.reply_text('Exiting sequence... (Type /start to reset sequence)', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    
def bake(bot,update):
    update.message.reply_text("In bake function")
    logger.info("User selected BAKE")

    
def main():
    print("D'easepenser is running...")
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            USER_CHOICE: [RegexHandler('^(Upload Recipe)$',
                                       enter_recipe_name),
                          RegexHandler('^(View Recipes)$',
                                       view_recipes),
                          RegexHandler('^(BAKE)$',
                                        bake)
                          ],
            
            RECIPE_NAME: [MessageHandler(Filters.text, enter_ingredients)],

            INPUT_TYPE: [MessageHandler(Filters.photo, image_to_text),
                         MessageHandler(Filters.text, text_to_text),
                         ],
            
            CONFIRMATION: [RegexHandler('^(Yes)$', enter_instructions),
                           RegexHandler('^(No)$', edit_entry),
                           MessageHandler(Filters.photo,image_to_text),
                           MessageHandler(Filters.text,text_to_text),
                           ],

            MAINMENU: [RegexHandler('^(Terminate)$', view_recipes),
                       RegexHandler('^(Main Menu)$', enter_recipe_name),
                       MessageHandler(Filters.text,view_recipes),
                       ]
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
    print("i am in the if main thing")
