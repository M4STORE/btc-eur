import telepot
from urllib.request import Request, urlopen
import time


def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'text':
        name = msg["from"]["first_name"]
        text = msg['text']

        # find input
        if '/help' in text:
            bot.sendMessage(chat_id, 'Hi %s, this bot finds current value of BTC-EUR trade' % name)
        elif '/start' in text:
            # bot.sendMessage(chat_id, 'Hi %s, just wait a little bit of time while I\'m preparing your data!' % name)

            url = 'https://it.investing.com/crypto/bitcoin/btc-eur'  # site where I get the data from

            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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

                bot.sendMessage(chat_id, result_message)

            else:
                bot.sendMessage(chat_id, "Sorry %s, I couldn't find the current prices for BTC")
                # if it can't find current price it will not print any other value (or try to find it)


TOKEN = '1684190706:AAEq_YBJPgn7cQxPu8DGUaZrlNjthH-6rzU'

bot = telepot.Bot(TOKEN)
bot.message_loop(on_chat_message)

print('Listening ...')  # just to know it's going and online





def handle_exception(exc):
    print("Error, probably timeout error")


while 1:   # has to stay here otherwise bot.message_loop(on_chat_message) won't work and program will stop
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        handle_exception(e)
    time.sleep(10)
