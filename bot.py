#telegram bot
import telepot

#http request / web interface
from urllib.request import Request, urlopen

#time
import time

#see if file is empty
import os

#dict to file library
import json

#EMAIL libraries
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def on_chat_message(msg):
    global step

    content_type, chat_type, chat_id = telepot.glance(msg)

    check_new_id(chat_id, msg["from"]["first_name"])

    if content_type == 'text':
        name = msg["from"]["first_name"]
        text = msg['text']

        # available commands
        if text == '/help':
            str_to_send = 'Hi %s, this bot finds current value of BTC-EUR trade and can send alerts through email' \
                          'if the price overtakes current min or max prices,\navailable commands are "/start" and "/sendalert"' % name

            send(chat_id, str_to_send)
        elif text == '/start':
            # bot.sendMessage(chat_id, 'Hi %s, just wait a little bit of time while I\'m preparing your data!' % name)

            str_to_send = calculate_data(url)

            send(chat_id, str_to_send)

        elif text == '/sendalert':

            send(chat_id, "Hi %s, insert your email to get alerts of BTC-EUR exchange prices" % name)

            step = 2

        elif step == 2:

            step = 1

            email = text

            if check_real_email(email, chat_id) and not check_existing_email(email) :
                add_email(email, chat_id)  #adds email to current chat_id
            else:
                if check_existing_email(email):
                    send(chat_id, "Email address already present")

    else:
        send(chat_id, "Hi %s, please insert text as input" % msg["from"]["first_name"])


def calculate_data(url):

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})   # else it has problem (Permission denied)
    openpage = urlopen(req).read()


    stringpage = str(openpage)  # openpage is of type "bytes", it could also be used to find substring but it is better to cast (has more methods like split, count...)

    if 'alertValue" placeholder' in stringpage:
        substr_price = stringpage.split('alertValue" placeholder')[1][:30]  # it first splits the html page and then takes only the first x characters from the split point

        if 'value="' in substr_price:
            substr_price = substr_price.split('value="')[1]  # just takes out unimportant data
            str_price = substr_price.split('"')[0]  # FIRST OUTPUT DATA

        min_and_max_day_price = ''
        # now tries to take out other data: MIN and MAX price of the day
        if 'Min-Max gg' in stringpage:
            min_price = ''
            max_price = ''

            substr_minmax_price = stringpage.split('Min-Max gg')[1][:142]

            if 'low' in substr_minmax_price:  # if not in split [1] we might have an error
                min_price = substr_minmax_price.split('low">')[1][:8]  # directly taking the number instead of splitting another time
            if 'high' in substr_minmax_price:
                max_price = substr_minmax_price.split('high">')[1][:8]

            min_and_max_day_price = 'Min price = '
            if min_price == '':
                min_and_max_day_price = "Coudn't get min price "
            else:
                min_and_max_day_price += min_price + ' '

            min_and_max_day_price += 'Max price = '
            if max_price == '':
                min_and_max_day_price += "Coudn't get max price "
            else:
                min_and_max_day_price += max_price

        # DATE
        date = ''
        if '-time">' in stringpage:
            date = stringpage.split('-time">')[1][:8]  # goes from 0 to 7-th place, so have to use 8

        # percentage decrease/increase price
        dec_inc = ''
        if 'parentheses" dir="ltr">' in stringpage:
            dec_inc = stringpage.split('parentheses" dir="ltr">')[1][0:8]
            dec_inc = dec_inc.split('<')[0]  # here we might have (if is later changed) one more character for '+' or '-'
            # if there will be no more '+', so we have to split the string and can't only take x number of chars

        # now we have collected all the data we wanted and can send them through Telegram
        if date != '':
            result_message = 'Date: ' + date + '\n\n'

        result_message += 'CURRENT PRICE: ' + str_price  # PRICE

        if min_and_max_day_price != '':  # note that we might have found only min or max and not both but could still send them
            result_message += '\n\n' + min_and_max_day_price
        if dec_inc != '':
            if '+' or '-' in dec_inc:
                if dec_inc[0] == '+':
                    result_message += '\nIncreased: ' + dec_inc
                else:
                    result_message += '\nDecreased: ' + dec_inc
            else:
                result_message += '\nChange percentage: ' + dec_inc

        return result_message

    else:
        # if it can't find current price it will not print any other value (or try to find it)
        str_to_send = "Sorry %s, I couldn't find the current prices for BTC"

        return str_to_send


#SEND FROM BOT

def send(chat_id, string_to_send):
    bot.sendMessage(chat_id, string_to_send)


#ID

def check_new_id(chat_id, chat_name):
    with open("database.txt", "r") as ids:
        str_data = ids.read()
        data = json.loads(str_data)

        for key, value in data.items():  # keys are the ids
            if str(chat_id) == str(key):
                return

    # send welcome message
    send(chat_id, 'Hi %s, this bot finds current value of BTC-EUR trade,\navailable commands are "/help", "/start" and "/sendalert"' % chat_name)

    # add chat_id to file (those are users who have already visited the bot)
    add_id(chat_id)


def add_id(chat_id):
    # reads data, changes the database and then overwrites the file

    with open("database.txt", "r") as file:
        str_data = file.read()
        data = json.loads(str_data)

    key = chat_id
    data.setdefault(key,
                    [])  # associates the key with a list of values and not only one value and also adds the key (with a corresponding empty list)

    with open("database.txt", "w") as file:
        json.dump(data, file)


#EMAIL

def check_existing_email(email):
    with open("database.txt", "r") as file:
        str_data = file.read()
        data = json.loads(str_data)

        for key in data:   # key are the ids
            for mail in data[key]:    # searching in a list
                if mail == email:    # if I check whether chat_id == key then someone might find a way to put infinite ids and infinite emails
                    return True

    return False


def check_real_email(email, chat_id):
    if '@' not in email or '.' not in email or email.index('@') == 0 or email.index('.') == 0 or email.index('@') == (email.index('.') - 1):
        send(chat_id, "Sorry, you have inserted a non valid email")
        return False
    else:
        return True


def add_email(email, chat_id):
    with open("database.txt", "r") as file:
        str_data = file.read()
        data = json.loads(str_data)

    for key, value in data.items():
        if str(key) == str(chat_id):  # it will sure find it because if there wasn't already that id it has just been created by add_id
            # don't actually know why without casting to string they don't match (key == chat_id) but this works

            if len(data[key]) >= 5:
                send(chat_id, "Sorry, you have inserted too much emails")
            else:
                data[key].append(email)

    with open("database.txt", "w") as file:
        json.dump(data, file)


def send_email_alert(data, prevdata, data_type):
    str_email_subject = "BTC-EUR price alert"
    str_send_email = "Hi, BTC_EUR HAS REACHED NOW A "

    if data_type == 'min':
        str_send_email += "MIN"
    else:
        str_send_email += 'MAX'

    str_send_email += 'NEW VALUE: ' + str(prevdata) + ' PREVIOUS VALUE: ' + str(data)


    #preparing session
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port    IT IS ALWAYS THE SAME BECAUSE THIS ARE THE SENDER DATA
    session.starttls()  # enable security
    session.login(sender_address, sender_pass)  # login with mail_id and password WHICH ARE GLOBAL (don't need to pass them in function)


    #preparing message
    message = MIMEMultipart()

    message['Subject'] = str_email_subject  # The subject line

    with open("database.txt", "r") as file:
        str_data = file.read()
        data = json.loads(str_data)

        for key, value in data.items():
            for mail in data[key]:
                message['From'] = sender_address
                message['To'] = mail

                message.attach(MIMEText(str_send_email, 'plain'))

                text = message.as_string()
                session.sendmail(sender_address, mail, text)

    #logout from sender address
    session.quit()


def handle_exception(exc):
    pass
    # print("Error, probably timeout error")


def update_min_max(change_min, change_max):
    calc_str = calculate_data(url)

    if "Coudn't get min price " not in calc_str:  # means that it has found the min part
        min = float((calc_str.split('Min price = ')[1]).split(',')[
                        0])  # split's two time (second time uses the space after min_price)

        if change_min == 0:
            change_min = min
        elif min - change_min < -200:  # value has gone under the previous max
            send_email_alert(min, change_min, "min")

            change_min = min
            # else the current min is not less than the previous one


    if "Coudn't get max price " not in calc_str:
        max = float((calc_str.split('Max price = ')[1]).split(',')[0])

        if change_max == 0:
            change_max = max
        elif max - change_max > 200:  # value has gone above the previous max
            change_max = max

            send_email_alert(max, change_max, "max")

    return change_min, change_max


def try_bot_polling():
    try:
        bot.polling(none_stop=True)  # tries not to make the bot stop after x minutes (if there are no messages Telegram/Heroku make it stop)
    except Exception as e:
        handle_exception(e)


# GLOBAL VARIABLES
update_time = 60



sender_address = 'therocktradingbtceur@gmail.com'
sender_pass = 'therock@01'

url = 'https://it.investing.com/crypto/bitcoin/btc-eur'  # site where I get the data from


TOKEN = '1684190706:AAEq_YBJPgn7cQxPu8DGUaZrlNjthH-6rzU'

bot = telepot.Bot(TOKEN)

bot.message_loop(on_chat_message)


# !!SUPPOSES THAT THE FILE EXISTS (better suppose it exists than to create it myself)
if os.stat("database.txt").st_size == 0:   # means that file is empty
    with open("database.txt", "w") as file:  # don't actually need to append anything
        database = {}  # creating whole database with chat_id and emails connected with it

        json.dump(database, file)  # have to use json.dump in order to save a dictionary to a file (otherwise I could have used file.write)


print('Listening ...')  # just to know it's going and online


start_time = -update_time
change_min = 0
change_max = 0

while 1:   # has to stay here otherwise bot.message_loop(on_chat_message) won't work and program will stop

    if time.time() - start_time > update_time:  # 60 seconds == 1 minute
        change_min, change_max = update_min_max(change_min, change_max)

    try_bot_polling()  # tries not to make the bot stop

    time.sleep(10)
