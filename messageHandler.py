

import re
import requests
from urllib3 import Retry
from CustomException import CustomException
from lineMessagePublisher import LineMessagePublisher
from postgresRepo import PostgresRepo
import unicodedata
import lssUtils
from dateutil import parser
import json
import copy
from itertools import groupby
from operator import itemgetter
import random

lineMessagePublisher = LineMessagePublisher()
repo = PostgresRepo()

REMINDER_HELP_MESSAGE = """
To create a new reminder, type #reminder with some name for the reminder. 
For e.g. '#reminder gate hit'. I will then help you with the rest of setup. 
\nYou can view your reminders anytime by typing '#reminder view'
\n To view today's agenda in this group, type '#reminder today'
"""
REMINDER_USER_CAP_EXCEEDED = "You cannot create any more reminders. Type '#reminder view' and delete one"
REMINDER_GROUP_CAP_EXCEEDED = "No more reminders can be created in this group. Those who have created reminders in the group need to type '#reminder view' and delete one"
SHEETS = ['https://docs.google.com/spreadsheets/u/0/d/15agdiOBHWqdHBU25h3dEiMdU0chlMOE9-1ntuaTbFas/htmlview#gid=1563202928',
          'https://docs.google.com/spreadsheets/u/0/d/1cedigmua5q4xoetEMFSDoCpQbKRw-h-yzOKt0YykSC0/htmlview#']

HOURLY_URL = 'https://lssnfo.com/'
LOADER_GIF = 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Youtube_loading_symbol_1_(wobbly).gif'
INBOX = 'Read your inbox messages you fucking bellend'
FETISH = 'Robot fetish is my thing on pornhub'


ADMINS = ['Uf85852359e1f99af7ef93fe57c24a56f',
          'Uea91e284551fc42fc968304ab3190a7d']

CURRENT_ADMIN_COMMANDS = """
Welcome admin! Currently you can run the following commands:

#admin guides add +<section> +<title> +<link> : adds a new guide entry under the specified section, with the title entered which links to the specified link
#admin guides remove +<section> +<title> : remove guide with entered section and title
"""

REMINDER_MAX_USER_COUNT = 2
REMINDER_MAX_GROUP_COUNT = 4
HELP_COMMAND = """
Greetings, my fellow comrades! I am LSS Bot V2, the younger brother of LSS Bot, and like him, I'm destined to make your LSS lives easier. Type in any of the
following commands with the hashtag:

#heroes
Everything on heroes and more!

#sheets
Spreadsheets having everything you would ever need!

#gt
Current game time

#hourly
Have a look at the hourly schedule for today and the week!

#dd
Everything about doomsday and eden!

#bb
Info on baneblade!

#ce
Info on Cutting edge tech!

#guides
Tips, tricks and useful guides on various topics of the game!

#feedback 
Share your thoughts, feedback or suggestions for the bot!

#help 
See this message again!
"""


class MessageHandler:

    def handleMessage(self, message):

        if (not 'text' in message['events'][0]['message']):
            return

        command = message['events'][0]['message']['text'].lower().strip()
        replyToken = message['events'][0]['replyToken']

        # print("userId: " + message['events'][0]
        #       ['source']['userId'] + " message: " + command)

        # asyncNotifyReminder = threading.Thread(self.notifyReminderAsync(replyToken, message), args=())
        # asyncNotifyReminder.start()

        # dad joke handler
        if (command == '#joke' or command == '#dadjoke' or command == "#felsa"):
            joke = self.getDadJoke()
            joke = self.cleanString(joke)
            lineMessagePublisher.sendTextMessage(replyToken, joke)
            # self.notifyReminder()
            return
        # tag handler
        elif (command == '#team'):
            # testProf = lineMessagePublisher.getUserProfile(message['events'][0]['source']['userId'])
            # print(testProf.json())

            audi = lineMessagePublisher.getUserProfile(
                'Uf85852359e1f99af7ef93fe57c24a56f')
            lene = lineMessagePublisher.getUserProfile(
                'Ua9009674673bea3617b82dd85611072b')
            felsa = lineMessagePublisher.getUserProfile(
                'U742315a44b4f60c840f035c400e0d147')
            bacon = lineMessagePublisher.getUserProfile(
                'U4dee0241023078dca338e55089154c7e')
            eric = {'displayName': 'EricLeKing',
                    'pictureUrl': 'https://i.pinimg.com/originals/ae/ec/24/aeec244b636ee48382f3e1a62bc5f64f.jpg'}

            lineMessagePublisher.sendFlexTeamMessage(
                replyToken, lene.json(), felsa.json(), audi.json(), bacon.json(), eric)
            # lineMessagePublisher.tagUsers(replyToken, "hello " + "{@"+message['events'][0]['source']['userId'] +"}" + "{" +message['events'][0]['source']['userId'] +"}")
            # lineMessagePublisher.tagUsers(self.getGroupId(message), message['events'][0]['source']['userId'], profile.json()['displayName'])
            # self.notifyReminder()
            return

        elif (command.startswith('#nude')):
            url = ''
            userId = message['events'][0]['source']['userId']

            if ('roomId' in message['events'][0]['source']):
                groupId = message['events'][0]['source']['roomId']
                url = 'https://api.line.me/v2/bot/room/' + groupId + '/member/' + userId

            elif ('groupId' in message['events'][0]['source']):
                groupId = message['events'][0]['source']['groupId']
                url = 'https://api.line.me/v2/bot/group/' + groupId + '/member/' + userId

            else:
                groupId = message['events'][0]['source']['userId']
                url = 'https://api.line.me/v2/bot/profile/' + userId

            response = lineMessagePublisher.callLineGetApi(url)
            data = response.json()

            lineMessagePublisher.sendImage(replyToken, data['pictureUrl'])
            return

        elif (command == '#nude' or command == '#nudes' or command == '#boobs'):
            lineMessagePublisher.sendImage(replyToken, LOADER_GIF)
            # self.notifyReminder()
            return

        elif (command == '#ass'):
            lineMessagePublisher.sendTextMessage(
                replyToken, 'Yes, you are an ass')
            # self.notifyReminder()
            return

        elif (command in ['#lendolf', '#inbox']):
            lineMessagePublisher.sendTextMessage(replyToken, INBOX)
            # self.notifyReminder()
            return

        elif (command in ["#hourly", "#hourlies"]):
            lineMessagePublisher.sendTextMessage(replyToken, HOURLY_URL)
            # self.notifyReminder()
            return

        elif (command in ['#sheet', '#sheets']):
            lineMessagePublisher.sendMultipleTextMessages(
                replyToken, SHEETS)

        elif (command in ["#porn", "#pornhub", '#sextape']):
            lineMessagePublisher.sendTextMessage(replyToken, FETISH)
            # self.notifyReminder()
            return

        # reminder handler
        elif (command.startswith('#reminder')):
            if (command == '#reminder'):
                message = self.getReminderHelpMessage()
                lineMessagePublisher.sendTextMessage(replyToken, message)
                return
            elif (command == '#reminder view'):
                reminders = self.getReminders(message)
                if (len(reminders) == 0):
                    lineMessagePublisher.sendTextMessage(
                        replyToken, "You don't have any reminders in this chat. Create one now!")
                else:
                    lineMessagePublisher.sendReminderCarousel(
                        replyToken, reminders, message['events'][0]['source']['userId'])
                return
            elif (command == '#reminder today'):
                currentGt = lssUtils.currentGameTime()
                reminders = self.getRemindersForTodayInGroup(
                    message, currentGt)
                lineMessagePublisher.sendReminderCalender(
                    replyToken, reminders, currentGt)
                return
            elif (command.startswith('#reminder ')):
                subject = unicodedata.normalize(
                    'NFC', command.replace('#reminder', '').strip())
                try:
                    if (self.validateReminder(message, subject)):
                        lineMessagePublisher.sendQuickReplyForReminder(
                            replyToken, message, subject)
                except CustomException as e:
                    lineMessagePublisher.sendTextMessage(replyToken, str(e))

                return
            return

        # GT handler
        elif (command == '#gt' or command == '#gametime'):
            lineMessagePublisher.sendTextMessage(
                replyToken, "current game time: " + str(lssUtils.currentGameTime().strftime("%d %B %Y %H:%M")))
            return

        elif (command in ["#hero", '#heroes', '#heros']):
            lineMessagePublisher.sendFlexMessage(
                replyToken, './hero_view.json', 'hero guide')
            return
        elif (command == '#help'):
            lineMessagePublisher.sendTextMessage(replyToken, HELP_COMMAND)
            return
        elif (command == '#feedback'):
            lineMessagePublisher.sendTextMessage(
                replyToken, 'If you have any feedback or suggestions for the bot, feel free to fill out this survey! \n https://forms.gle/WcEFA8kdP3ebqCTe9')
            return

        elif (command.startswith("#compliment ")):
            compliment = self.getCompliment()
            compliment = self.cleanString(compliment)
            name = command.replace("#compliment ", "").strip()
            message = name.title() + ", " + compliment
            lineMessagePublisher.sendTextMessage(replyToken, message)
            return

        elif (command.startswith("#insult ")):
            insult = self.getInsult()
            insult = self.cleanString(insult)
            name = command.replace("#insult ", "").strip()
            message = name.title() + ", " + insult
            lineMessagePublisher.sendTextMessage(replyToken, message)
            return

        elif (command.startswith("#flirt ")):
            pickupline = self.getPickupLine()
            pickupline = self.cleanString(pickupline)
            name = command.replace("#flirt ", "").strip()
            message = name.title() + ", " + pickupline
            lineMessagePublisher.sendTextMessage(replyToken, message)
            return

        elif (command == '#rock'):
            lineMessagePublisher.sendRockImageMap(replyToken)
            return

        elif (command == '#trivia'):
            data = self.getTriviaQuestion()
            # print(data)
            lineMessagePublisher.sendTriviaMessage(replyToken, data)
            return

        elif(command in ['#dd', '#doomsday', '#eden']):
            lineMessagePublisher.sendFlexMessage(
                replyToken, './dd_view.json', 'Doomsday Menu')
            return

        elif(command == '#bb'):
            lineMessagePublisher.sendImage(
                replyToken, 'https://www.lastshelter.eu/BB-Extended.png')
            return

        elif(command in ['#guide','#guides']):
            guidesData = self.getGuidesData()
            guideJson = self.createGuidesJson(guidesData)
            lineMessagePublisher.sendFlexMessageJson(
                replyToken, guideJson, 'Guides')
            return

        elif(command == '#ce'):
            image = {}
            url = 'https://cdn.discordapp.com/attachments/727102227952435211/852013537958428742/1611095296091.jpg'
            image['type'] = 'image'
            image['originalContentUrl'] = url
            image['previewImageUrl'] = url

            textMessage = {}
            textMessage['type'] = 'text'
            textMessage['text'] = 'war badge calculator: \n' + \
                'https://cdn.discordapp.com/attachments/736457247877496847/830122392990515240/Cutting_Edge_Calculator_V3.1.xlsx'

            pointCalculator = {}
            pointCalculator['type'] = 'text'
            pointCalculator['text'] = 'cutting edge point planner: \n' + \
                'http://mycodezoo.com/lss/en/ce_points_planner.php'

            jsonMessage = {}
            jsonMessage['replyToken'] = replyToken
            jsonMessage['messages'] = [image, textMessage, pointCalculator]

            lineMessagePublisher.sendJsonReplyMessage(jsonMessage)
            return

        elif(command.startswith('#admin ')):
            userId = message['events'][0]['source']['userId']
            if(userId not in ADMINS):
                lineMessagePublisher.sendTextMessage(
                    replyToken, 'Sorry, you are not an admin')
                return
            else:
                print("admin")
                if (command == '#admin help'):
                    lineMessagePublisher.sendTextMessage(
                        replyToken, CURRENT_ADMIN_COMMANDS)
                    return

                elif (message['events'][0]['message']['text'].strip().startswith('#admin guides add ')):
                    guideCommand = message['events'][0]['message']['text'].replace(
                        '#admin guides add', "").strip()
                    guideCommand = guideCommand.split(' +')
                    print(guideCommand)
                    if (len(guideCommand) != 3):
                        lineMessagePublisher.sendTextMessage(
                            replyToken, 'admin guide command not entered correctly. Type #admin help')
                        return

                    url = guideCommand[2]
                    if (not self.validateUrl(url)):
                        lineMessagePublisher.sendTextMessage(
                            replyToken, url + ' is an invalid URL')
                        return

                    section = guideCommand[0].strip().replace('+', '').title()
                    title = guideCommand[1].strip().replace('+', '')

                    repo.insertGuidesRecord(section, title, url)

                    lineMessagePublisher.sendTextMessage(
                        replyToken, 'new guide added. check #guides')
                    return

                elif (command.startswith('#admin guides remove ')):
                    guideCommand = command.replace(
                        '#admin guides remove', "").strip()
                    guideCommand = guideCommand.split(' +')
                    if (len(guideCommand) != 2):
                        lineMessagePublisher.sendTextMessage(
                            replyToken, 'admin guide command not entered correctly. Type #admin help')
                        return

                    section = guideCommand[0].strip().replace('+', '').title()
                    title = guideCommand[1].strip().replace('+', '')

                    repo.deleteGuideRecord(section, title)

                    lineMessagePublisher.sendTextMessage(
                        replyToken, 'guide deleted. check #guides')
                    return

                return

        elif(command in ['#morning', '#coffee', '#goodmorning']):
            response = requests.get(url="https://coffee.alexflipnote.dev/random.json")
            lineMessagePublisher.sendImage(replyToken, response.json()['file'])
            return

        elif(command in ['#bitch']):
            lineMessagePublisher.sendTextMessage(replyToken, "I am Audi's bitch")
            return

        elif(command.startswith('#love')):
            lineMessagePublisher.sendTextMessage(replyToken, 'https://youtu.be/24e-B00iiws')
            return
        
        elif(command == '#beer'):
            lineMessagePublisher.sendImage(replyToken, 'https://raw.githubusercontent.com/audi1/lssStuff/main/621091.jpg')
            return

        elif(command == '#burn'):
            lineMessagePublisher.sendTextMessage(replyToken, 'https://youtu.be/i1ojUmdF42U')
            return

        # elif(command == '#rose'):
        #     rockImages = [
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/108908.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/108918.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/108932.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/108941.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/108989.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/429863.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/S__24249265.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/S__24249267.jpg',
        #         'https://raw.githubusercontent.com/audi1/lssStuff/main/rock/S__24249268.jpg'
        #     ]


        #     lineMessagePublisher.sendImage(replyToken, random.choice(rockImages))
        #     return
            
    def getGuidesData(self):
        res = repo.getGuidesJson()
        # print(res)
        return res

    def createGuidesJson(self, guidesData):
        with open('./guides_view.json') as f:
            jsonObject = json.load(f)

            guideList = []
            for guide in guidesData:
                guideDataAsJson = {'section':guide[1], 'title':guide[2], 'url':guide[3]}
                guideList.append(guideDataAsJson)

            # print(guideList)

            guideList = sorted(guideList, key = itemgetter('section'))

            for key, value in groupby(guideList, key=itemgetter('section')):

                sectionToAdd = {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                            {
                                "type": "text",
                                "text": key,
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0,
                                "weight": "bold"
                            }
                    ]
                }

                for val in value:
                    print(val)

                    contentElemToAdd = {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": val['title'],
                            "uri": val['url']
                        },
                        "style": "link",
                        "offsetStart": "none",
                        "offsetEnd": "none",
                        "margin": "none"
                    }

                    sectionToAdd['contents'].append(contentElemToAdd)
                
                jsonObject['body']['contents'][1]['contents'].append(
                        copy.deepcopy(sectionToAdd))

            return jsonObject

    def validateUrl(self, url):
        try:
            requests.get(url)
            return True
        except:
            return False

    def sendWelcomeMessage(self, message):
        lineMessagePublisher.sendTextMessage(
            message['events'][0]['replyToken'], 'Welcome! Type #help to see all of the bot commands')
        return

    def getMessageContent(self, messageId):
        response = lineMessagePublisher.callLineGetApi(
            'https://api-data.line.me/v2/bot/message/' + messageId + '/content')
        return response

    def getTriviaQuestion(self):
        response = requests.get(
            url="https://opentdb.com/api.php?amount=1&type=multiple", headers={"Accept": "application/json"})
        data = response.json()['results'][0]

        triviaData = {}
        triviaData['question'] = self.cleanString(data['question'])
        triviaData['correct_answer'] = self.cleanString(data['correct_answer'])
        triviaData['incorrect_answers'] = []
        for i in range(0, len(data['incorrect_answers'])):
            triviaData['incorrect_answers'].append(
                self.cleanString(data['incorrect_answers'][i]))

        return triviaData

    def cleanString(self, string):
        string = str(string)
        string = string.strip()
        string = string.replace('&quot;', "\"")
        string = string.replace('&#039;', "\'")

        return unicodedata.normalize('NFC', string)

    def getDadJoke(self):
        response = requests.get(
            url="https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
        return response.json()['joke']

    def getCompliment(self):
        response = requests.get(
            url="https://complimentr.com/api/", headers={"Accept": "application/json"})
        return response.json()['compliment']

    def getInsult(self):
        response = requests.get(
            url="https://evilinsult.com/generate_insult.php?lang=en&amp;type=json", headers={"Accept": "application/json"})
        return response.text

    def getPickupLine(self):
        response = requests.get(
            url='http://getpickuplines.herokuapp.com/lines/random', headers={"Accept": "application/json"}
        )

        return response.json()['line']

    def getReminderHelpMessage(self):
        return REMINDER_HELP_MESSAGE

    def getReminders(self, message):
        reminders = []
        reminderRecords = repo.getReminders(
            message['events'][0]['source']['userId'], self.getGroupId(message))
        for reminderRecord in reminderRecords:
            reminder = {}
            reminderId = reminderRecord[0]
            reminderTime = reminderRecord[4]
            reminderTime = reminderTime.strftime("%d %B %Y %H:%M")
            reminderString = reminderRecord[3] + \
                "\n" + "At " + str(reminderTime)
            reminder['reminderString'] = reminderString
            reminder['id'] = reminderId

            reminders.append(reminder)

        return reminders

    def getRemindersForTodayInGroup(self, message, gameTime):
        reminders = []
        reminderRecords = repo.getRemindersForTodayInGroup(
            self.getGroupId(message), gameTime)
        for reminderRecord in reminderRecords:
            reminderId = reminderRecord[0]
            reminderTime = reminderRecord[4]
            reminderTime = reminderTime.strftime("%H:%M")
            reminderString = reminderRecord[3]

            reminder = {'reminderTime': reminderTime,
                        'reminderMsg': reminderString, 'id': reminderId}

            reminders.append(reminder)

        return reminders

    def validateReminder(self, message, subject):

        if (len(subject) > 100):
            raise CustomException("reminder message is too long!")

        elif (len(subject) < 1):
            raise CustomException("no message entered")

        userId = message['events'][0]['source']['userId']
        # print(userId)
        # print(message['events'][0])
        userCount = repo.getUserCount(userId)

        if (userCount > REMINDER_MAX_USER_COUNT):
            raise CustomException(REMINDER_USER_CAP_EXCEEDED)

        groupCount = repo.getUserCount(self.getGroupId(message))

        if (groupCount > REMINDER_MAX_GROUP_COUNT):
            raise CustomException(REMINDER_GROUP_CAP_EXCEEDED)

        return True

    def handlePostback(self, message):

        dataString = message['events'][0]['postback']['data']

        dataSet = dict(p.split('=') for p in dataString.split('&') if p)
        # print(dataSet)

        replyToken = message['events'][0]['replyToken']
        if (dataSet['type'] == "reminderCallback"):
            try:
                confirmation = self.setReminder(message, dataSet)
                lineMessagePublisher.sendTextMessage(replyToken, confirmation)
            except CustomException as e:
                lineMessagePublisher.sendTextMessage(replyToken, str(e))
        elif (dataSet['type'] == "deleteReminder"):
            reminder = repo.getReminderByReminderId(dataSet['reminderId'])
            if reminder:
                if reminder[0]:
                    # print(str(reminder[0][1]))
                    # print(str(message['events'][0]['source']['userId']))
                    if (str(reminder[0][1]) != str(message['events'][0]['source']['userId'])):
                        lineMessagePublisher.sendTextMessage(
                            replyToken, "You cannot delete a reminder created by someone else, you sneaky weasel")
                        return
            deleteCount = self.deleteReminder(dataSet['reminderId'])
            if (deleteCount > 0):
                lineMessagePublisher.sendTextMessage(
                    replyToken, "Reminder deleted!")
            else:
                lineMessagePublisher.sendTextMessage(
                    replyToken, "Reminder was deleted before")
        elif (dataSet['type'] == 'triviaCallback'):
            if (dataSet['ans'] == 'correct'):
                lineMessagePublisher.sendTextMessage(
                    replyToken, 'Congratulations, you got the right answer!')
                return
            elif (dataSet['ans'] == 'incorrect'):
                lineMessagePublisher.sendTextMessage(
                    replyToken, 'Sorry, wrong answer! Correct answer is ' + dataSet['correct_ans'])
                return

    def setReminder(self, message, data):
        repo.insertReminderRecord(data['userId'], data['groupId'], data['message'],
                                  message['events'][0]['postback']['params']['datetime'])

        datetime = parser.parse(
            message['events'][0]['postback']['params']['datetime'])
        datetime = datetime.strftime("%d %B %Y %H:%M")
        return "Created reminder: " + data['message'] + ".\n" + "I will bug you at " + str(datetime) + " game time"

    def deleteReminder(self, reminderId):
        return repo.deleteReminder(reminderId)

    def getGroupId(self, message):
        if ('roomId' in message['events'][0]['source']):
            groupId = message['events'][0]['source']['roomId']

        elif ('groupId' in message['events'][0]['source']):
            groupId = message['events'][0]['source']['groupId']

        else:
            groupId = message['events'][0]['source']['userId']

        return groupId

    def notifyReminder(self):
        gameTime = lssUtils.currentGameTime().strftime("%Y-%m-%dT%H:%M")
        records = repo.getReminderByTime(gameTime)
        if records:
            for record in records:
                if record:
                    groupId = record[2]
                    message = record[3]
                    lineMessagePublisher.sendPushTextMessage(
                        groupId, " ------------------- \n REMINDER:\n" + message + "\n ------------------- \n ")
                    print("found reminder to notify:")
                    print(record)
                    self.deleteReminder(record[0])
        # repo.getReminders()

    def notifyReminderAsync(self, replyToken, chatMessage):
        try:
            gameTime = lssUtils.currentGameTime().strftime("%Y-%m-%dT%H:%M")
            # print("in async method")
            records = repo.getReminderByTime(gameTime)
            if records:
                for record in records:
                    if record:
                        groupId = record[2]
                        chatGroupId = self.getGroupId(chatMessage)
                        if groupId == chatGroupId:
                            message = record[3]
                            lineMessagePublisher.sendTextMessage(
                                replyToken, " ------------------- \n REMINDER:\n" + message + "\n ------------------- \n ")
                            print("found reminder to notify:")
                            print(record)
                            self.deleteReminder(record[0])
        except Exception as e:
            print("--------- exception at notifyReminderAsync: " + str(e))
        # print("async method done")
