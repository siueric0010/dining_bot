 # import libraries
from bs4 import BeautifulSoup
#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
import tokens
import requests
import json

# import libraries (pymessenger = Bot)
import os, sys
from flask import Flask, request
from pymessenger import Bot
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

app = Flask(__name__)

PAGE_ACCESS_TOKEN = tokens.PAGE_ACCESS_TOKEN
VERIFICATION_TOKEN = tokens.VERIFICATION_TOKEN
base_url = 'https://hdh-web.ucsd.edu'

#cap = DesiredCapabilities().FIREFOX
#cap["marionette"] = False

#options = Options()
#options.headless = True

#browser = webdriver.Firefox(options=options, executable_path=r'/app/geckodriver')
#browser = webdriver.PhantomJS("/app/phantomjs-2.1.1-linux-i686/bin/")
#browser.get(base_url)
#print ("Headless Firefox Initialized")

bot = Bot(PAGE_ACCESS_TOKEN)

def send_text_quick_replies(recipient_id, listOfReplies, messageToReplyTo, listOfPayloads=[]):
  """
  Sends a list of text quick replies with an optional message to send before sending the quick replies
  Payload and Message are optional, however, if no payload for a specific reply (i.e. None) 
  or for all quick replies, the payload will be defined as the reply itself.


  https://developers.facebook.com/docs/messenger-platform/send-messages/quick-replies/#text

  Output:
      Response from API as <dict>
  """
  quickRepliesList = []

  # If no payloads identified
  if len(listOfPayloads) == 0:     
    for reply in listOfReplies:
      quickRepliesList.append({
                              "content_type":"text",
                              "title":reply,
                              "payload":reply
                              })

  # If payloads is identified
  else:
    for reply, payload in zip(listOfReplies, listOfPayloads):
      # if some payload is not identified in the list
      if payload == None:
        quickRepliesList.append({
                                "content_type":"text",
                                "title":reply,
                                "payload":reply
                                })
      if payload != None:
        quickRepliesList.append({
                                "content_type":"text",
                                "title":reply,
                                "payload":payload
                                })

      # if the length of payloads is less than replies, then just let the payload for the rest to be just the reply
      if len(listOfPayloads) < len(listOfReplies):
        for reply in listOfReplies[len(listOfPayloads):]:
          quickRepliesList.append({
                                  "content_type":"text",
                                  "title":reply,
                                  "payload":reply
                                  })
  return bot.send_message(recipient_id, {
          "text": messageToReplyTo,
          "quick_replies": quickRepliesList
          })





@app.route('/', methods=['GET'])
# Webhook validation
def verify():
	if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
		if not request.args.get("hub.verify_token") == VERIFICATION_TOKEN:
			return "Verification token mismatch", 403
		return request.args["hub.challenge"], 200
	return "Success!", 200

@app.route('/', methods=['POST'])
def webhook():
  data = request.get_json()
  from pprint import pprint
  pprint(data)
  if data['object'] == 'page':
    for entry in data['entry']:
      for messaging_event in entry['messaging']:
        id = messaging_event['sender']['id']
        '''
        if messaging_event.get('postback'):
          print("test")
          if messaging_event['postback'].get('payload'):
            if messaging_event['postback']['payload'] == 'Yes':
              bot.send_text_message(id, "You clicked Yes")
            if messaging_event['postback']['payload'] == 'No':
              bot.send_text_message(id, "You clicked No")
            return 'OK', 200
        '''
        if messaging_event.get('message'):
          if messaging_event['message'].get('text'):
            # Find link
            dictionaryOfLinks = {}
            r = requests.get('https://hdh-web.ucsd.edu/dining/apps/diningservices/')
            soup = BeautifulSoup(r.text, "html.parser")
            facilityNames = soup.findAll("div", class_="facility-name")
            for name in facilityNames:
              var = name.find("a")
              restaurantName = var.text[:-2]
              restaurantName = restaurantName.strip()
              restaurantAppendLink = var['href']
              if "Restaurant" in restaurantAppendLink:
                dictionaryOfLinks[restaurantName] = restaurantAppendLink
              
            
            user_text = messaging_event['message']['text']
            quickRepliesList = []
            listOfReplies =[]
            for restaurantName in dictionaryOfLinks:
              listOfReplies.append(restaurantName)
            send_text_quick_replies(id, listOfReplies, "What restaurants do you want to check?")
            

            """
            for restaurantName in dictionaryOfLinks:
              quickRepliesList.append({
                                        "content_type":"text",
                                        "title":restaurantName,
                                        "payload":restaurantName
                                     })
            
            bot.send_message(id, {
              "text": "What restaurant do you want to check?",
              "quick_replies": quickRepliesList
            })
          
            """
            
          if messaging_event['message'].get('quick_reply'):
            if messaging_event['message']['quick_reply']['payload'] in dictionaryOfLinks:
              payloadText = messaging_event['message']['quick_reply']['payload']
              # Find link
              dictionaryOfLinks = {}
              r = requests.get('https://hdh-web.ucsd.edu/dining/apps/diningservices/')
              soup = BeautifulSoup(r.text, "html.parser")
              facilityNames = soup.findAll("div", class_="facility-name")
              for name in facilityNames:
                var = name.find("a")
                restaurantName = var.text[:-2]
                restaurantName = restaurantName.strip()
                restaurantAppendLink = var['href']
                if "Restaurant" in restaurantAppendLink:
                  dictionaryOfLinks[restaurantName] = restaurantAppendLink
              link = base_url + dictionaryOfLinks[payloadText]

              # GETS MENU AT LINK #
              r = requests.get(link)
              soup = BeautifulSoup(r.text, "html.parser")
              mainAppData = soup.find("script", type="text/javascript")
              string = mainAppData.text            

              list = string.split(",", -1)
              concateStringBreakfast = "Breakfast:\n\n" 
              concateStringLunch = "Lunch:\n\n"
              concateStringDinner= "Dinner:\n\n"
              passedFood = False
              listBreakfast = []
              listLunch = []
              listDinner = []
              tempFoodName = ""
              for item in list:            
                # Check Breakfast/Lunch/Dinner Items
                if "tag" in item:
                  if "BREAKFAST" in item and passedFood and tempFoodName not in listBreakfast:
                    listBreakfast.append(tempFoodName)
                  if "LUNCH" in item and passedFood and tempFoodName not in listLunch:
                    listLunch.append(tempFoodName)
                  if "DINNER" in item and passedFood and tempFoodName not in listDinner:
                    listDinner.append(tempFoodName)
                    #del listPrint[-1]

                # Assign all the food to a list
                if "name" in item:
                  itemSplit = item.split("\":\"")
                  itemName = itemSplit[1][0:-1]
                  tempFoodName = itemName
                  passedFood = True

              # connect all the items    
              for item in listBreakfast:
                concateStringBreakfast += item + "\n"
              for item in listLunch:
                concateStringLunch += item + "\n"
              for item in listDinner:
                concateStringDinner += item + "\n"

              bot.send_text_message(id, concateStringBreakfast)
              bot.send_text_message(id, concateStringLunch)
              bot.send_text_message(id, concateStringDinner)
              # END OF SENDING MENU #
            
              
  return 'OK', 200
  
  

if __name__ == "__main__":
  app.run()
  

            