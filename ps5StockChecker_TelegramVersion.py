import telebot
import time
import requests
import json
import random
import psutil

### input/preference data ###

token = #enter your telegram bot token here
admin_chat_id = #enter your telegram chat id here
channel_id = #enter your channel id here
bot = telebot.TeleBot(token)
message = "PS5 Available at {}!\nHere's the link: {}"
stanbyTime = 15 # in seconds (must be an integer)

### input/preference data END ###


### functions ###

def should_i_check(store_data, count):
    ''' Determines wether to perform check or not based on "check_frequecy_scaling_constant" and current "count" '''
    return count % store_data['check_frequecy_scaling_constant'] == 0

def getHTML(store_data):
    ''' Returns HTML code from url of store listing '''

    resp = requests.get(store_data['url'], headers = store_data['headers'], timeout = 20)
    html = resp.text
    
    return html

def initialise_store_data_list(store_data_list):
    ''' Initialises "store_data_list" '''
    for store_data in store_data_list:
        store_data['last_resp_invalid'] = False
        store_data['consecutive_invalid_responses'] = 0
        
def getCount(count):
    ''' Returns incremented "count" variable. Resets on overflow (i.e. when "count" reaches 100). "count" variable required for scaling how frequently program checks websites indivisually (Eg. Flipkart every 15 secs and Amazon every 30 secs)'''
    
    if count >= 100:
        count = 1
    else:
        count += 1
    
    return count

def standby(stanbyTime):
    ''' Provides delay between consequent retailer website checks '''

    print('                 \r', end='')
    for i in range(stanbyTime):
        for postfix in ['   ','.  ','.. ','...']:
            print("Standby" + postfix + '\r',end='')
            time.sleep(0.25)
    
    print('Checking Stock in a few seconds...\r', end='')
    time.sleep(random.uniform(0.0,3.0)) #provides some randomisation to delay between each request (to seem more human), in hopes that retailer doesnt figure out that this is a bot
    print('Checking Stock...                 \r',end='')

def check(html, store_data):
    ''' Checks if PS5 is in stock. Also monitors when website returns a wierd response and notifies on telegram when consequent wierd responses excede 10 '''
    
    html_lower = html.lower()
    check_string = store_data['check_string'].lower()
    verify_string = store_data['secondary_verify_string'].lower()
    
    if check_string in html_lower:
    
        print('Stock Detected!   ',end='\n\n')
    
        bot.send_message(channel_id, message.format(store_data['store_name'], store_data['url']))
        
        if store_data['last_resp_invalid']:
            store_data['last_resp_invalid'] = False
            store_data['consecutive_invalid_responses'] = 0
    
    elif verify_string not in html_lower:
    
        print('ERROR: Someting wrong with {} server response. Retrying in a few seconds.\n\n'.format(store_data['store_name']), end='')
        
        store_data['last_resp_invalid'] = True
        store_data['consecutive_invalid_responses'] += 1
        
        if store_data['consecutive_invalid_responses'] > 10:
            bot.send_message(admin_chat_id, 'More than 10 consecutive invalid responses from {} server encountered'.format(store_data['store_name']))
    
    elif store_data['last_resp_invalid']:
        store_data['last_resp_invalid'] = False
        store_data['consecutive_invalid_responses'] = 0
    
def checkBattery():
    ''' Checks battery and notifies on telegram if battery is low and unplugged or if battery is almost full and plugged in '''

    battery = psutil.sensors_battery()
    
    batteryLow = battery.percent <= 15
    batteryHigh = battery.percent >= 95
    pluggedIn = battery.power_plugged
    
    if batteryLow and not pluggedIn:
        bot.send_message(admin_chat_id, 'Laptop battery has dipped to 15%. Please plug it in.')
    elif batteryHigh and pluggedIn:
        bot.send_message(admin_chat_id, 'Laptop battery has reached 95%. Please disconnect it to avoid overcharging.')

### functions END ###

# "count" tracks the number of iterations performed in inifinite loop below, resets to 1 on reaching 100. Helps to scale how frequently retailers are checked indivisually (Eg. Flipkart every 15 secs while Amazon every 30 secs)
count = 1 #initialising count variable

#loading ps5 listings
with open('ps5_listings_data.json') as f:
    store_data_list = json.load(f)
    initialise_store_data_list(store_data_list)

print('''
PlayStation 5 Stock Bot
''')

while True:
    
    try:
        for store_data in store_data_list:
        
            if should_i_check(store_data, count):
                
                html = getHTML(store_data)
                
                check(html, store_data)
        checkBattery()

    except:
        print('ERROR: Unknown error encountered. Retrying in a few seconds.\n\n', end='')
    
    count = getCount(count)
    
    standby(stanbyTime)