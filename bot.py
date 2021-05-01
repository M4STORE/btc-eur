# telegram bot
#import telepot

import ciao as telep

# time
import time

# threads
from _thread import *



# message loop
from loop import MessageLoop

# dict to file library
import json

# keyboards
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import bot_tasks
import drive


def on_chat_message(msg):
    global step
    global emailandtelegr
    global is_premium
    global updating_files


    type = msg['chat']['type']

    #if type == "private":
    #    pass
    #    # message from msg['chat']['first_name']
    #elif type == "group":
    #    pass
    #elif type == "supergroup":
    #    pass
    # elif type == "channel":
    #    pass
    #else:
    #    return

    content_type, chat_type, chat_id = telep.glance(msg)

    # message from msg['chat']['title']


    check_shutdown_file(True, chat_id)

    if updating_files:
        send(chat_id, "Hi, I'm updating all daily files, I will be available in a few seconds/one minute")
        return



    res = mybot_user.check_new_id("alerts.txt", msg["from"]["first_name"], chat_id)

    markup = on_settings_msg(chat_id)

    mybot.sendMessage(chat_id, 'Choose your settings', reply_markup=markup)





    if  res != None:
        send(chat_id, res)

    if content_type == 'text':
        name = msg["from"]["first_name"]
        text = msg['text']

        # available commands
        if text == '/help':
            str_to_send = 'Hi %s, ' % name

            send(chat_id, str_to_send)

            step = 1

        elif text == '/start':
            markup = on_start_msg(chat_id)

            mybot.sendMessage(chat_id, 'Select one crypto', reply_markup=markup)


            step = 1  # in case the user input /sendalert and then start, step is always 2,
                      # so if he then inputs random text the bot will say email not valid

        elif text == '/settings':  # manually open settings keyboard
            markup = on_settings_msg(chat_id)

            mybot.sendMessage(chat_id, 'Choose your settings', reply_markup=markup)
        elif text == "/refresh":
            refresh_files()

        elif text == '₿📈 GET CRYPTO PRICES 🤑':
            markup = on_start_msg(chat_id)

            mybot.sendMessage(chat_id, 'Select one crypto', reply_markup=markup)

        elif text == 'ADD 💶 OR REMOVE 💸 CRYPTO':
            markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='💰 ADD 💰'), KeyboardButton(text='💸 REMOVE 💸')], [KeyboardButton(text='❌ BACK ❌')], ])
            mybot.sendMessage(chat_id, 'Do you want to ADD or REMOVE?', reply_markup=markup)

        elif text == '✉️ CHANGE ALERT TYPE ⏰':
            with open("alerts.txt", "r") as file:
                alert_dict = json.loads(file.read())

            pers_alert = alert_dict[str(chat_id)]


            if pers_alert[0].split("-")[0] == "premium":
                is_premium = True
                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📧 EMAIL 📧'), KeyboardButton(text='📧 EMAIL AND TELEGRAM 📱'),
                                                        KeyboardButton(text='📱 TELEGRAM 📱'), KeyboardButton(text='💤 NO ALERT 💤')], [KeyboardButton(text='❌ BACK ❌')], ])
                mybot.sendMessage(chat_id, 'Select the type of alert', reply_markup=markup)
            else:
                is_premium = False

                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📱 TELEGRAM 📱'), KeyboardButton(text='💤 NO ALERT 💤')], [KeyboardButton(text='❌ BACK ❌')], ])
                mybot.sendMessage(chat_id, 'Select the type of alert', reply_markup=markup)

        elif text == '❌ BACK ❌':
            pass

        elif text == '📧 EMAIL 📧' or text == '📧 EMAIL AND TELEGRAM 📱':
            send(chat_id, "Ok, insert the email")


            if text == "EMAIL":
                emailandtelegr = False
            else:
                emailandtelegr = True

            step = 3

        elif text == '📱 TELEGRAM 📱':

            with open("alerts.txt", "r") as file:
                alert_dict = json.loads(file.read())

            if alert_dict[str(chat_id)][0].split("-")[1] != "telegram":
                if is_premium == True:
                    if "email" in alert_dict[str(chat_id)][0] or "both" in alert_dict[str(chat_id)][0]:
                        alert_dict[str(chat_id)][1] = ""

                    alert_dict[str(chat_id)][0] = "premium-telegram"
                else:
                    if "email" in alert_dict[str(chat_id)][0] or "both" in alert_dict[str(chat_id)][0]:
                        alert_dict[str(chat_id)][1] = ""

                    alert_dict[str(chat_id)][0] = "normal-telegram"


                with open("alerts.txt", "w") as file:
                    json.dump(alert_dict, file)

                start_new_thread(mydrive.delete_file, ("alerts.txt", None))
                start_new_thread(mydrive.upload_file_to_root_dir, ("alerts.txt",))

                send(chat_id, "Alert state successfully changed")
            else:
                send(chat_id, "Alert state was already set to 'telegram'")



        elif text == '💤 NO ALERT 💤':

            with open("alerts.txt", "r") as file:
                alert_dict = json.loads(file.read())

            if alert_dict[str(chat_id)][0].split("-")[1] != "none":
                if is_premium == True:
                    if "email" in alert_dict[str(chat_id)][0] or "both" in alert_dict[str(chat_id)][0]:
                        alert_dict[str(chat_id)][1] = ""

                    alert_dict[str(chat_id)][0] = "premium-none"
                else:
                    if "email" in alert_dict[str(chat_id)][0] or "both" in alert_dict[str(chat_id)][0]:
                        alert_dict[str(chat_id)][1] = ""

                    alert_dict[str(chat_id)][0] = "normal-none"


                with open("alerts.txt", "w") as file:
                    json.dump(alert_dict, file)

                send(chat_id, "Alert state successfully changed")


                start_new_thread(mydrive.delete_file, ("alerts.txt", None))
                start_new_thread(mydrive.upload_file_to_root_dir, ("alerts.txt", ))
            else:
                send(chat_id, "Alert state was already set to 'no alerts'")


        elif text == '🗣️ GIVE SOME ADVICE 📖':
            send(chat_id, "Hi, you can give us advice by typing '/advice your_advice'")

        elif text == '🔥 GET PREMIUM VERSION 🔥':
            send(chat_id, "Sorry, Premium Version not developed yet")

        elif "/advice" in text:
            if text.split("/advice")[1] != "":
                with open("advices.txt", "r") as file:
                    advices_dict = json.loads(file.read())

                if str(chat_id) not in advices_dict:
                    advices_dict.setdefault(str(chat_id), [])

                advices_dict[str(chat_id)].append(text.split("/advice")[1])

                with open("advices.txt", "w") as file:
                    json.dump(advices_dict, file)

                send(chat_id, "Advice saved")

                start_new_thread(mydrive.delete_file, ("advices.txt", None))
                start_new_thread(mydrive.upload_file_to_root_dir, ("advices.txt",))

                mybot_tasks.send_email_alert(mybot_tasks.myemail_data()[0], mybot_tasks.myemail_data()[1], "New", "Advice on cryptos-bot", text.split("/advice")[1], "easynewmymail@gmail.com", True)

            else:
                send(chat_id, "Sorry, invalid advice")


        elif step == 3:
            step = 1

            new_email = text

            if mybot_user.check_real_email(new_email, chat_id) == False:
                send(chat_id, "Sorry, you have inserted an invalid email")
            else:

                with open("alerts.txt", "r") as file:
                    alert_dict = json.loads(file.read())

                if "email" in alert_dict[str(chat_id)][0] or "both" in alert_dict[str(chat_id)][0]:
                    alert_dict[str(chat_id)][1] = new_email
                else:
                    alert_dict[str(chat_id)].append(new_email)

                if emailandtelegr == False:
                    alert_dict[str(chat_id)][0] = "premium-email"
                else:
                    alert_dict[str(chat_id)][0] = "premium-both"



                with open("alerts.txt", "w") as file:
                    json.dump(alert_dict, file)

                send(chat_id, "Email successfully added and alert state changed")

                start_new_thread(mydrive.delete_file, ("alerts.txt", None))
                start_new_thread(mydrive.upload_file_to_root_dir, ("alerts.txt", ))

        elif text == '💸 REMOVE 💸':
            with open("personalcryptos.txt", "r") as file:
                pers_cryptos = json.loads(file.read())

            cryptos = pers_cryptos[str(chat_id)]

            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'{str(crypto).upper()}', callback_data=f'remove/{crypto}')] for crypto in cryptos])

            mybot.sendMessage(chat_id, 'Choose the one you want to remove', reply_markup=markup)


        elif text == '💰 ADD 💰':
            with open("cryptos.txt", "r") as file:
                all_cr_dict = json.loads(file.read())


            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=f'{str(crypto).upper()}', callback_data=f'add/{crypto}')]
                                 for crypto in all_cr_dict])

            mybot.sendMessage(chat_id, 'Choose the one you want to add', reply_markup=markup)

        else:
            send(chat_id, "Sorry, unrecognizable input")

    else:
        send(chat_id, "Hi %s, please insert text as input" % msg["from"]["first_name"])


def on_start_msg(chat_id):
    with open("personalcryptos.txt", "r") as file:
        pers_dict = json.loads(file.read())

    with open("cryptos.txt", "r") as file:
        cr_dict = json.loads(file.read())

    pers_cryptos = pers_dict[str(chat_id)]


    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'{crypto}', callback_data=f'{str(crypto).upper()}')] for crypto in pers_cryptos])

    return markup


def on_settings_msg(chat_id):
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='₿📈 GET CRYPTO PRICES 🤑')],
        [KeyboardButton(text='ADD 💶 OR REMOVE 💸 CRYPTO'), KeyboardButton(text='✉️ CHANGE ALERT TYPE ⏰')],
        [dict(text='🗣️ GIVE SOME ADVICE 📖'), KeyboardButton(text='🔥 GET PREMIUM VERSION 🔥')], ])

    return markup


def on_callback_query(msg):
    query_id, chat_id, query_data = telep.glance(msg, flavor='callback_query')

    query_data = str(query_data).lower()
    #print('Callback Query:', query_id, chat_id, query_data)

    with open("cryptos.txt", "r") as file:
        cr_dict = json.loads(file.read())

    if query_data in cr_dict.keys():
        mybot_tasks.calculate_data(mybot_tasks.create_url(cr_dict[str(query_data)], str(query_data)), mybot, chat_id, True)
        markup = on_start_msg(chat_id)

        mybot.sendMessage(chat_id, 'Select one crypto', reply_markup=markup)

    elif query_data == "all":
        with open("personalcryptos.txt", "r") as file:
            pers_dict = json.loads(file.read())

        pers_cryptos = pers_dict[str(chat_id)]

        for crypto in pers_cryptos:
            if crypto != "all":
                mybot_tasks.calculate_data(mybot_tasks.create_url(cr_dict[str(crypto)], str(crypto)), mybot, chat_id, True)

       #markup = on_start_msg(chat_id)
       #
       #mybot.sendMessage(chat_id, 'Select one crypto', reply_markup=markup)
        
    elif "remove/" in str(query_data):
        query_data = query_data.split("/")[1]
        res = mybot_tasks.manage_key_dict(chat_id, query_data, "personalcryptos.txt", "remove")

        markup = on_settings_msg(chat_id)

        mybot.sendMessage(chat_id, f'{res}', reply_markup=markup)

    elif "add/" in str(query_data):
        query_data = query_data.split("/")[1]
        res = mybot_tasks.manage_key_dict(chat_id, query_data, "personalcryptos.txt", "add")

        markup = on_settings_msg(chat_id)

        mybot.sendMessage(chat_id, f'{res}', reply_markup=markup)


# SEND FROM BOT

def send(chat_id, string_to_send):
    mybot.sendMessage(chat_id, string_to_send)


def check_shutdown_file(is_message_loop = None, chat_id = None):
    global updating_files
    # verifies it exists  NOTE THAT IT HAS TO EXIST LOCALLY OTHERWISE IT HAS NO POINT IN BEING DELETED EVERY DAY
    try:
        with open("shutdown.txt", "r") as file:
            pass
    except:
        print("shutdown file not found!!!")   # it has no sense to create it now (would be deleted)

        raise FileNotFoundError

    with open("shutdown.txt", "r") as file:
        check = file.readline()

    if check == "0":   # Heroku has shut down server and value in shutdown file is "0" (the static one)
        # downloads all files (which have been changed)
        updating_files = True

        if is_message_loop:
            send(chat_id, "Hi, I'm updating all daily files, I will be available in a few seconds/one minute")

            refresh_files()

        updating_files = False  # put here because if readfile fails this will be always true


def refresh_files():
    all_files_name = ["alerts.txt", "personalcryptos.txt", "prices.txt", "advices.txt"]


    for filename in all_files_name:
        file_content = mydrive.read_file(filename)

        if file_content == "{}":
            data_dict = {}
        else:
            data_dict = json.loads(file_content)

        with open(filename, "w") as file:  # overwrites local files
            json.dump(data_dict, file)


    with open("shutdown.txt", "w") as file:
        file.write("1")







def handle_exception(exc):
    pass
    # print("Error, probably timeout error")


def try_bot_polling():
    try:
        mybot.polling(
            none_stop=True)  # tries not to make the bot stop after x minutes (if there are no messages Telegram/Heroku make it stop)
    except Exception as e:
        handle_exception(e)





# GLOBAL VARIABLES

update_time = 60*5
start_time = -update_time

update_check_time = 60   # controls if heroku has shut down the server, in that case downloads all files from drive and overwrites them locally
check_file_start_time = -update_check_time

step = 1

emailandtelegr = False
is_premium = False

updating_files = False


# CLASSES OBJECTS

mybot_tasks = bot_tasks.BotOnlyTasks()
mybot_user = bot_tasks.UserBotRelationship()
mydrive = drive.GoogleDriveClass()


mybot = telep.Bot(mybot_tasks.read_token())


MessageLoop(mybot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()


def main_loop():
    global start_time
    global check_file_start_time

    while 1:  # has to stay here otherwise bot.message_loop(on_chat_message) won't work and program will stop
        if time.time() - check_file_start_time > update_check_time:
            check_shutdown_file()

            check_file_start_time = time.time()

        if time.time() - start_time > update_time:  # 60 seconds == 1 minute
            try:
                mybot_tasks.update_all_prices(mybot)
                start_time = time.time()
            except Exception as e:
                print(e)


        try_bot_polling()  # tries not to make the bot stop

        time.sleep(10)


#time.sleep(10)

print('Listening ...')  # just to know it's going and online

main_loop()