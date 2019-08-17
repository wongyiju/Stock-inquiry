#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 11:09:13 2019

@author: wyz
"""

import string
import re
import random
from iexfinance.stocks import Stock
from iexfinance.stocks import get_historical_data
from datetime import datetime
import spacy
import sys

# Load the spacy model: nlp, en_core_web_md
nlp = spacy.load("en_core_web_md")
## Using spaCy's entity recogniser

# Define included entities
include_entities = ['DATE', 'ORG', 'PERSON']

# Define extract_entities()
def extract_entities(message):
    # Create a dict to hold the entities
    ents = dict.fromkeys(include_entities)
    # Create a spacy document
    doc = nlp(message)
    for ent in doc.ents:
        if ent.label_ in include_entities:
            # Save interesting entities
            ents[ent.label_] = ent.text
    return ents

# Define chitchat_response()
def chitchat_response(message):
    # Call match_rule()
    response, phrase = match_rule(rules, message)
    # Return none is response is "default"
    if response == "default":
        return None
    if '{0}' in response:
        response = response.format(phrase)
    return response

def match_rule(rules, message):
    for pattern, responses in rules.items():
        match = re.search(pattern, message)
        if match is not None:
            response = random.choice(responses)
            var = match.group(1) if '{0}' in response else None
            return response, var
    return "default", None

rules = {'thank(.*)': ["My pleasure"], 
         'what can (.*)': ["I'm a robot to help you get information about stock"], 
         'bye(.*)': ['Ok, bye']
        }


def send_message(state, pending, message, comp):
    message = message.lower()
    response = chitchat_response(message)
    if response is not None:
        print(response)
        if response == 'Ok, bye':
            sys.exit(0)
        return state, None, comp
    
    if item_idetification(message) == 'historical':
        state = CHOOSE_DATE
        new_state, response, pending_state = policy_rules[(state, 'historical')]
    elif interpret(message) is not None:
        new_state, response, pending_state = policy_rules[(state, interpret(message))]
    elif interpret(message) is None:
        new_state, response, pending_state = state, "Sorry, I can't catch you.", None
    if interpret(message) == 'specify_company':
        comp = company_identification(message)
        response = response.format(comp)
    if interpret(message) == 'specify_item':
        info = Stock(comp,token="pk_910d4c5b9a2d4d379af7260ae8e549f2")
        item = item_idetification(message)
        API_search = None
        if item == 'low' or item == 'high' or item == 'latestPrice' or item == 'volume':
            API_search = info.get_quote()[item]
            response = response.format(item, API_search)
        if item == 'logo':
            API_search = info.get_logo()['url']
            response = response.format(item, API_search)
    if interpret(message) == 'date':
        date = extract_entities(message)['DATE']
        if datetime.strptime(date,'%Y %m %d').weekday() == 0 or datetime.strptime(date,'%Y %m %d').weekday() == 6:
            response = "Sorry. I can only find stock information on weekdays."
        else:
            start = datetime(2015, 1, 1)
            end = datetime(2019, 8, 14)
            API_search = get_historical_data('AAPL', start, end, output_format='pandas',token="pk_910d4c5b9a2d4d379af7260ae8e549f2")
            date_dict = API_search.loc[date]
            date_message = "open price: {0}, high price: {1}, low price: {2}, close price: {3}, total volume: {4}".format(date_dict['open'],date_dict['high'],date_dict['low'],date_dict['close'],date_dict['volume'])
            response = response.format(date_message)
    print(response)
    if pending is not None and interpret(message) == 'number':
        new_state, response, pending_state = policy_rules[pending]
        print(response)        
    if pending_state is not None:
        pending = (pending_state, interpret(message))
    return new_state, pending, comp

def company_identification(message):
    if 'aapl' in message or 'appl' in message or 'aple' in message:
        return 'AAPL'
    if 'googl' in message or 'gogl' in message:
        return 'GOOGL'
    if 'berry' in message or 'bb' in message or 'black' in message:
        return 'BB'
    if 'hp' in message or 'hewlett' in message or 'packard' in message:
        return 'HPQ'
    if 'ibm' in message or 'international business machines' in message:
        return 'IBM'
    if 'nok' in message or 'nokia' in message:
        return 'NOK'
    if 'msft' in message or 'micro' in message:
        return 'MSFT'
    if 'baidu' in message or 'bidu' in message:
        return 'BIDU'
    if 'baba' in message or 'ali' in message:
        return 'BABA'
    if 'sina' in message or 'xinlang' in message:
        return 'SINA'
    if 'sohu' in message or 'souhu' in message:
        return 'SOHU'
    if 'ntes' in message or 'netease' in message:
        return 'NTES'
    return None

def item_idetification(message):
    if 'low' in message:
        return 'low'
    if 'high' in message:
        return 'high'
    if 'price' in message:
        return 'latestPrice'
    if 'volume' in message:
        return 'volume'
    if 'logo' in message:
        return 'logo'
    if 'historical' in message:
        return 'historical'
    return None

def interpret(message):  
    if '201' in message:
        return 'date'
    elif item_idetification(message) is not None:
        return 'specify_item'
    elif company_identification(message) is not None:
        return 'specify_company'
    elif 'stock' in message:
        return 'search'
    if any([d in message for d in string.digits]) and '201' not in message:
        return 'number'
    return None

# Define the states
INIT=0
AUTHED=1
CHOOSE_COMPANY=2
CHOOSE_ITEM=3
CHOOSE_DATE=4
DATE_DONE=5

# Define the policy rules
policy_rules = {
    (INIT, "search"): (INIT, "You'll have to log in first, what's your phone number?", AUTHED),
    (INIT, "number"): (AUTHED, "Perfect, welcome back!", None),
    (AUTHED, "search"): (CHOOSE_COMPANY, "Which company would you like to know about?", None),  
    (CHOOSE_COMPANY, "specify_company"): (CHOOSE_ITEM, "What kind of stock information for {0} would you like to see?", None),
#choose item, the second is to back to choose company
    (CHOOSE_ITEM, "specify_item"): (CHOOSE_ITEM, "Ok! The {0} is {1}", None),
    (CHOOSE_ITEM, "specify_company"): (CHOOSE_ITEM, "What kind of stock information for {0} would you like to see?", None),
#choose historical, the second is to back to choose item, the third is to back to choose company
    (CHOOSE_DATE, "historical"): (DATE_DONE, "Ok! But you have to tell me the date first.", None),
    (CHOOSE_DATE, "specify_item"): (CHOOSE_ITEM, "Ok! The {0} is {1}", None),
    (CHOOSE_DATE, "specify_company"): (CHOOSE_ITEM, "What kind of stock information for {0} would you like to see?", None),
#choose date, the second is to back to choose historical, the third is to back to choose item, the fourth is to back to choose company
    (DATE_DONE, "date"): (DATE_DONE, "Ok! Here you are: {0}", None),
    (DATE_DONE, "historical"): (DATE_DONE, "Ok! But you have to tell me the date first.", None),
    (DATE_DONE, "specify_item"): (CHOOSE_ITEM, "Ok! The {0} is {1}", None),
    (DATE_DONE, "specify_company"): (CHOOSE_ITEM, "What kind of stock information for {0} would you like to see?", None)
}


state = INIT
pending = None
comp = None
info = None
x = 1
while x<= 100:
    message = input("Please input:")
    state, pending, comp = send_message(state, pending, message, comp)
    x += 1
print ("You are tired. Please take a break.")

'''
Example:
# Send the messages
send_messages([
    "What can you do for me?",
    "I'd like to search for some stock info",
    "555-12345",
    "i need some information about Apple",
    "volume", 
    "what about the lowest price",
    "ok, then what about some information about Google",
    "price",
    "hhhhhhhhhhhhhhhhhhh",
    "i want some historical information",
    "i want some information on 2018 5 6",
    "ok, then what about info on 2019 4 9",
    "ok, then back to AAPL",
    "i wanna knnow the logo of apple",
    "what about the price"
])
'''
