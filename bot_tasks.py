# time
import time

# see if file is empty
import os

# dict to file library
import json

# threads
from _thread import *

# EMAIL libraries
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# http request / web interface
from urllib.request import Request, urlopen

from drive import GoogleDriveClass



class UserBotRelationship:
    def __init__(self):
        self.mydrive = GoogleDriveClass()
        self.mydrive.authentication()

        self.file_id = None
        self.dir_id = None
        self.email_to_add = None

    # EMAIL

    def check_real_email(self, email, chat_id):
        if '@' not in email or '.' not in email or email.index('@') == 0 or email.index('.') == 0 or email.index(
                '@') == (
                email.index('.') - 1):

            return False
        else:
            return True

    # ID

    def check_new_id(self, file_name, chat_name, chat_id):
        with open(file_name, "r") as file:
            alerts_dict = json.loads(file.read())

        message = None

        if str(chat_id) not in alerts_dict.keys():
            alerts_dict.setdefault(chat_id, [])
            alerts_dict[chat_id].append("normal-none")   # basic user
            alerts_dict[chat_id].append("")  # blank

            with open("alerts.txt", "w") as file:  # saves the new dict
                json.dump(alerts_dict, file)

            start_new_thread(self.mydrive.delete_file, ("alerts.txt", None))
            start_new_thread(self.mydrive.upload_file_to_root_dir, ("alerts.txt",))

            with open("personalcryptos.txt", "r") as file:
                pers_dict = json.loads(file.read())

            if str(chat_id) not in pers_dict:   # should always be true
                pers_dict.setdefault(chat_id, [])
                pers_dict[chat_id].append("all")

            with open("personalcryptos.txt", "w") as file:
                json.dump(pers_dict, file)

            start_new_thread(self.mydrive.delete_file, ("personalcryptos.txt", None))
            start_new_thread(self.mydrive.upload_file_to_root_dir, ("personalcryptos.txt",))

            # send welcome message
            message = f'Hi {chat_name}, this bot can tell you LIVE CRYPTO PRICES\nand it can SEND you via telegram or by email (only premium version),\n' \
                      f'live ALERTS when price of your chosen cryptos decreases or increases by 1000,\n\n' \
                      f'available commands are "/help", "/start", "/sendalert" and "/deletealert"'

            return message


    def create_new_folder(self, chat_id, mother_folder, name):
        self.mydrive.create_folder_in_folder(chat_id, mother_folder, str(name))









class BotOnlyTasks:
    def __init__(self):
        # ALL CRYPTOS

        self.cr_dict  = {}
        self.cr_dict["btc-eur"] = "bitcoin"
        self.cr_dict["btc-usd"] = "bitcoin"
        self.cr_dict["eth-eur"] = "ethereum"
        self.cr_dict["eth-usd"] = "ethereum"
        self.cr_dict["ada-usd"] = "cardano"
        self.cr_dict["zec-usd"] = "zcash"
        self.cr_dict["pdotn-usd"] = "polkadot-new"
        self.cr_dict["knc-usd"] = "kyber-network"
        self.cr_dict["zil-usd"] = "zilliqa"
        self.cr_dict["icx-usd"] = "icon"
        self.cr_dict["dash-usd"] = "dash"
        self.cr_dict["ksm-usd"] = "kusama"
        self.cr_dict["atom-usd"] = "cosmos"
        self.cr_dict["bat-usd"] = "basic-attention-token"
        self.cr_dict["fil-usd"] = "filecoin"
        self.cr_dict["xrp-usd"] = "xrp"
        self.cr_dict["xlm-usd"] = "stellar"
        self.cr_dict["erd-usd"] = "elrond-egld"
        self.cr_dict["doge-usd"] = "dogecoin"


        # PREVIOUS DATA MANAGEMENT
        self.bot_mydrive = GoogleDriveClass()
        self.bot_mydrive.authentication()

        self.bot_user_relat = UserBotRelationship()

        self.crypto_file_init()
        self.prices_file_init()
        self.alert_file_init()
        self.advices_file_init()
        self.personalcrypto_file_init()


        self.alert_change_price = 5  # 5%

    def read_token(self):
        with open("token.txt", "r") as file:
            TOKEN = file.read()

        return TOKEN


    def calculate_data(self, url, bot = None, chat_id = None, to_send_here = None):
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})  # else it has problem (Permission denied)
        openpage = urlopen(req).read()

        stringpage = str(
            openpage)  # openpage is of type "bytes", it could also be used to find substring but it is better to cast (has more methods like split, count...)

        if 'alertValue" placeholder' in stringpage:
            substr_price = stringpage.split('alertValue" placeholder')[1][
                           :30]  # it first splits the html page and then takes only the first x characters from the split point

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
                    min_price = substr_minmax_price.split('low">')[1][
                                :8]  # directly taking the number instead of splitting another time
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
                dec_inc = dec_inc.split('<')[
                    0]  # here we might have (if is later changed) one more character for '+' or '-'
                # if there will be no more '+', so we have to split the string and can't only take x number of chars

            # now we have collected all the data we wanted and can send them through Telegram
            result_message = str(url.split("/")[-1].upper()) + "\n"

            if date != '':
                result_message += 'Date: ' + date + '\n\n'

            result_message += 'CURRENT PRICE: ' + str(str_price)  # PRICE

            if min_and_max_day_price != '':  # note that we might have found only min or max and not both but could still send them
                result_message += '\n\n' + min_and_max_day_price
            if dec_inc != '':
                if '+' or '-' in dec_inc:
                    if dec_inc[0] == '+':
                        result_message += '\nIncreased 📈: ' + dec_inc
                    else:
                        result_message += '\nDecreased 📉: ' + dec_inc
                else:
                    result_message += '\nChange percentage: ' + dec_inc

            if to_send_here is True:
                bot.sendMessage(chat_id, result_message)
                return
            else:
                return result_message

        else:
            # if it can't find current price it will not print any other value (or try to find it)
            str_to_send = "Sorry %s, I couldn't find the current prices for BTC"

            if to_send_here is True:
                bot.sendMessage(chat_id, str_to_send)
                return
            else:
                return str_to_send


    def send_email_alert(self, sender_address, sender_pass, data, prevdata, str_send_email, receiver_email, advice = None):
        if advice:
            str_email_subject = "New advice cryptos-bot"
        else:
            str_email_subject = "BTC-EUR price alert"
            str_send_email += 'CURRENT VALUE: ' + str(data) + '\nPREVIOUS VALUE: ' + str(prevdata)

        # preparing session
        session = smtplib.SMTP('smtp.gmail.com',
                               587)  # use gmail with port    IT IS ALWAYS THE SAME BECAUSE THIS ARE THE SENDER DATA
        session.starttls()  # enable security
        session.login(sender_address,
                      sender_pass)  # login with mail_id and password WHICH ARE GLOBAL (don't need to pass them in function)

        # preparing message
        message = MIMEMultipart()

        message['Subject'] = str_email_subject  # The subject line


        message['From'] = sender_address
        message['To'] = receiver_email

        message.attach(MIMEText(str_send_email, 'plain'))

        text = message.as_string()
        session.sendmail(sender_address, receiver_email, text)

        # logout from sender address
        session.quit()


    def update_price(self, change_price, url, crypto_name, crypto_shortcut, mybot):
        calc_str = self.calculate_data(url)

        if "I couldn't find the current prices for BTC" not in calc_str:
            price = float(calc_str.split("CURRENT PRICE: ")[1].split(".")[0].replace(",", ""))
            decimal = float(calc_str.split("CURRENT PRICE: ")[1].split("\n")[0].split(".")[1])

            count = 0
            while count < 5:
                if decimal > 100:
                    decimal = int(decimal / 100)

                count += 1

            if decimal > 100:
                decimal = 0

        while decimal > 1:  # there can't be infinite loop
            decimal /= 10

        price += decimal


        if change_price == 0:
            change_price = price  # if file has just been created it will be always 0, so no mybot required
        elif (float(change_price) - price) / (price) * 100 < -self.alert_change_price:
            self.send_alert(price, change_price, str(crypto_shortcut),
                       f"Hi, {str(crypto_shortcut).upper()} has 📉 DECREASED 📉 its price by over %d from the last time\n" % self.alert_change_price, mybot)

            change_price = price
        elif (float(change_price) - price) / (price) * 100 > self.alert_change_price:
            self.send_alert(price, change_price, str(crypto_shortcut),
                       f"Hi, {str(crypto_shortcut).upper()} has 📈 INCREASED 📈 its price by over %d from the last time\n" % self.alert_change_price, mybot)

            change_price = price

        return change_price

    def update_all_prices(self, mybot = None):
        with open("prices.txt", "r") as price_file:
            try:
                data = json.loads(price_file.read())
            except:
                # print("Prices file is empty")
                self.prices_file_init()

        with open("cryptos.txt", "r") as crypto_file:
            try:
                crypto_dict = json.loads(crypto_file.read())
            except:
                self.crypto_file_init()

        new_data_dict = {}

        one_changed = False
        for key, value in crypto_dict.items():
            try:
                change_price = float(data[str(key)])
            except:
                change_price = 0  # HAD TO ADD THIS PART BECAUSE IT SEEMS THAT HEROKU DOESN'T EXECUTE THE OS.STAT PART ABOVE (CHECK IF FILE IS EMPTY)

            crypto_name = crypto_dict[str(key)]

            possible_new_change_price = self.update_price(change_price, self.create_url(crypto_name, key), crypto_name, key, mybot)


            if possible_new_change_price != change_price:
                one_changed = True
                new_data_dict[key] = str(possible_new_change_price)
            else:
                new_data_dict[key] = float(data[str(key)])  # == str(change_price)


        if one_changed == True:
            with open("prices.txt", "w") as price_file:
                json.dump(new_data_dict, price_file)

            start_new_thread(self.bot_mydrive.delete_file, ("prices.txt", None))
            start_new_thread(self.bot_mydrive.upload_file_to_root_dir, ("prices.txt",))



    def crypto_file_init(self):
        try:
            with open("cryptos.txt", "r") as file:
                data_dict = json.loads(file.read())
                pass
        except:
            with open("cryptos.txt", "w"):
                pass

        if os.stat("cryptos.txt").st_size == 0 or data_dict != self.cr_dict:
            with open("cryptos.txt", "w") as file:
                json.dump(self.cr_dict, file)



    def prices_file_init(self):
        try:
            with open("prices.txt", "r"):
                pass
        except:
            with open("prices.txt", "w"):
                pass

        if os.stat("prices.txt").st_size == 0:
            with open("cryptos.txt", "r") as file:
                try:
                    cr_dict = json.loads(file.read())
                except:
                    # print("Crypto file is empty")
                    self.crypto_file_init()

            void_prices_dict = {}
            for key, value in cr_dict.items():  # key is shortcut == identificator
                void_prices_dict[key] = "0"

            with open("prices.txt", "w") as file:
                json.dump(void_prices_dict, file)

            self.update_all_prices()

    def alert_file_init(self):
        try:
            with open("alerts.txt", "r"):
                pass
        except:
            with open("alerts.txt", "w"):
                pass

        if os.stat("alerts.txt").st_size == 0:  # means that file is empty
            with open("alerts.txt", "w") as file:  # don't actually need to append anything
                tdict = {}
                json.dump(tdict, file)

    def advices_file_init(self):
        try:
            with open("advices.txt", "r"):
                pass
        except:
            with open("advices.txt", "w"):
                pass

        if os.stat("advices.txt").st_size == 0:  # means that file is empty
            with open("advices.txt", "w") as file:  # don't actually need to append anything
                tdict = {}
                json.dump(tdict, file)


    def personalcrypto_file_init(self):
        try:
            with open("personalcryptos.txt", "r"):
                pass
        except:
            with open("personalcryptos.txt", "w"):
                pass

        if os.stat("personalcryptos.txt").st_size == 0:  # means that file is empty
            with open("personalcryptos.txt", "w") as file:  # don't actually need to append anything
                tdict = {}
                json.dump(tdict, file)

    def send_alert(self, old_price, new_price, cr_shortcut, message, mybot):
        try:
            with open("personalcryptos.txt", "r") as file:
                try:
                    pers_dict = json.loads(file.read())
                except:  # it is an empty dict
                    return

            users_to_send = []

            for key, value in pers_dict.items():
                if str(cr_shortcut) in value:
                    users_to_send.append(str(key))


            for user in users_to_send:
                with open("alerts.txt", "r") as file:
                    try:
                        alert_dict = json.loads(file.read())
                    except:  # it is an empty dict
                        return

                for key, value in alert_dict.items():
                    if str(user) == str(key):   # could have done alert_dict[key][0] but I wouldn't know if I had deleted manually some data in the file
                        if str(value[0]).split("-")[0] == "premium":
                            if str(value[0]).split("-")[1] == "both":
                                self.send_email_alert(self.myemail_data()[0], self.myemail_data()[1], new_price, old_price, message, str(value[1]))
                            elif str(value[0]).split("-")[1] == "email":
                                self.send_email_alert(self.myemail_data()[0], self.myemail_data()[1], new_price, old_price, message, str(value[1]))
                            elif str(value[0]).split("-")[1] == "telegram":
                                mybot.sendMessage(str(key), message + 'CURRENT VALUE: ' + str(new_price) + '\nPREVIOUS VALUE: ' + str(old_price))
                            else:  # "none"
                                pass
                        else:
                            if str(value[0]).split("-")[1] == "telegram":
                                mybot.sendMessage(str(key), message + 'CURRENT VALUE: ' + str(new_price) + '\nPREVIOUS VALUE: ' + str(old_price))
                            else:
                                pass
        except Exception as e:
            print(e)
            print("Couldn't open alert file")


    def create_url(self, name, shortcut):
        return f'https://www.investing.com/crypto/{name}/{shortcut}'


    def myemail_data(self):
        sender_address, sender_pass = None, None

        try:
            with open("myemail.txt", "r") as file:
                sender_address = file.readline()
                sender_pass = file.readline()
        except Exception as e:
            print(e)
            print("Couldn't get my email data")

        return sender_address, sender_pass

    def manage_key_dict(self, key, value, filename, task):
        msg = ""

        with open(filename, "r") as file:
            dict = json.loads(file.read())

        pers_cryptos = dict[str(key)]

        if task == "remove":
            for crypto in pers_cryptos:
                if str(value) == str(crypto):
                    dict[str(key)].remove(str(value))
                    msg = "Crypto removed"
                    break

        elif task == "add":
            for crypto in pers_cryptos:
                if str(value) == str(crypto):
                    msg = "Crypto already present"
                    return msg

            dict[str(key)].append(value)
            msg = "Crypto added successfully"


        self.save_new_dict_to_file(filename, dict)

        start_new_thread(self.bot_mydrive.delete_file, (filename, None))
        start_new_thread(self.bot_mydrive.upload_file_to_root_dir, (filename,))

        time.sleep(1)
        
        return msg

    def save_new_dict_to_file(self, filename, dict):
        with open(filename, "w") as file:
            json.dump(dict, file)

