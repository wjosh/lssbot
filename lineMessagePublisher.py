from types import coroutine
import requests
import os
import sys
import datetime
from dateutil.relativedelta import relativedelta
import lssUtils
import json
import copy
import random


class LineMessagePublisher:
    channel_access_token = os.environ.get('CHANNEL_ACCESS_TOKEN', None)
    if channel_access_token is None:
        print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
        sys.exit(1)

    def sendTextMessage(self, replyToken, message):
        textMessage = {}
        textMessage['type'] = 'text'
        textMessage['text'] = message

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [textMessage]

        self.sendJsonReplyMessage(jsonMessage)

    def sendMultipleTextMessages(self, replyToken, messages):
        textMessages = []
        for message in messages:
            textMessage = {'type': 'text', 'text': message}
            textMessages.append(textMessage)

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = textMessages

        print(jsonMessage)

        self.sendJsonReplyMessage(jsonMessage)

    def sendTriviaMessage(self, replyToken, data):
        quickReply = {}
        
        correctAns = {'type': 'action', 'action': {'type': 'postback', 'label': data['correct_answer'], 'data': 'type=triviaCallback&ans=correct', 'displayText': data['correct_answer']}}
        quickReply['items'] = [correctAns]

        for incorrectAns in data['incorrect_answers']:
            incorrectAnsOption = {'type': 'action', 'action': {'type': 'postback', 'label': incorrectAns, 'data': 'type=triviaCallback&ans=incorrect&correct_ans='+data['correct_answer'], 'displayText': incorrectAns}}
            quickReply['items'].append(incorrectAnsOption)
        
        textMessage = {}
        textMessage['type'] = 'text'
        textMessage['text'] = data['question']
        textMessage['quickReply'] = quickReply

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [textMessage]

        # print(jsonMessage)

        self.sendJsonReplyMessage(jsonMessage)

    def sendQuickReplyForReminder(self, replyToken, message, subject):
        quickReply = {}
        curr = lssUtils.currentGameTime()
        future = curr + relativedelta(months=+6)
        curr = curr.strftime("%Y-%m-%dT%H:%M")
        future = future.strftime("%Y-%m-%dT%H:%M")

        if ('roomId' in message['events'][0]['source']):
            groupId = message['events'][0]['source']['roomId']

        elif ('groupId' in message['events'][0]['source']):
            groupId = message['events'][0]['source']['groupId']

        else:
            groupId = message['events'][0]['source']['userId']

        data = 'type=reminderCallback&message='+subject+'&userId=' + \
            message['events'][0]['source']['userId']+'&groupId='+groupId

        dateTimePickerAction = {}
        dateTimePickerAction['type'] = 'datetimepicker'
        dateTimePickerAction['label'] = 'Select date and time'
        dateTimePickerAction['data'] = str(data)
        dateTimePickerAction['mode'] = 'datetime'
        dateTimePickerAction['initial'] = str(curr)
        dateTimePickerAction['min'] = str(curr)
        dateTimePickerAction['max'] = str(future)

        dateTimePicker = {}
        dateTimePicker['type'] = 'action'
        dateTimePicker['action'] = dateTimePickerAction

        quickReply['items'] = [dateTimePicker]

        textMessage = {}
        textMessage['type'] = 'text'
        textMessage['text'] = 'Choose date and time for reminder, in game time'
        textMessage['quickReply'] = quickReply

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [textMessage]

        # print(jsonMessage)

        self.sendJsonReplyMessage(jsonMessage)

    def callLineGetApi(self, api):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.channel_access_token
        }
        return requests.get(url=api, headers=headers)

    def sendJsonReplyMessage(self, json):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.channel_access_token
        }
        return requests.post(url='https://api.line.me/v2/bot/message/reply', headers=headers, json=json)

    def sendPushTextMessage(self, to, message):
        textMessage = {}
        textMessage['type'] = 'text'
        textMessage['text'] = message

        jsonMessage = {}
        jsonMessage['to'] = to
        jsonMessage['messages'] = [textMessage]

        # print("SENDING PUSH NOTIFS")
        # print(jsonMessage)
        self.sendJsonPushMessage(jsonMessage)

    def sendJsonPushMessage(self, json):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.channel_access_token
        }
        return requests.post(url='https://api.line.me/v2/bot/message/push', headers=headers, json=json)

    def sendReminderCarousel(self, replyToken, reminders, userId):
        bgColors = ['#FF6B6E', '#A17DF5', '#27ACB2']

        carousel = {}
        carousel['type'] = 'carousel'

        carouselItems = []
        with open('./reminder_view.json') as f:
            jsonObject = json.load(f)
            for i in range(0, len(reminders)):
                baseContent = {}
                baseContent = jsonObject
                baseContent['header']['backgroundColor'] = bgColors[(i % 3)]
                baseContent['header']['contents'][0]['text'] = reminders[i]['reminderString']
                baseContent['body']['contents'][0]['contents'][0]['action']['data'] = 'type=deleteReminder&userId=' + \
                    userId + '&reminderId=' + str(reminders[i]['id'])

                contentCopy = copy.deepcopy(baseContent)

                carouselItems.append(contentCopy)

        carousel['contents'] = carouselItems

        flexMessage = {}
        flexMessage['type'] = 'flex'
        flexMessage['altText'] = 'reminders'
        flexMessage['contents'] = carousel

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [flexMessage]

        self.sendJsonReplyMessage(jsonMessage)

    def getGroupMembers(self, groupId):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.channel_access_token
        }

        return requests.get(url='https://api.line.me/v2/bot/group/' + groupId + '/members/ids', headers=headers)

    def getUserProfile(self, userId):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.channel_access_token
        }

        return requests.get(url='https://api.line.me/v2/bot/profile/' + userId, headers=headers)

    def sendImage(self, replyToken, url):
        image = {}
        image['type'] = 'image'
        image['originalContentUrl'] = url
        image['previewImageUrl'] = url

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [image]

        self.sendJsonReplyMessage(jsonMessage)

    def sendFlexMessageJson(self, replyToken, json, altText):
        jsonMessage = {}
        flexMessage = {}
        flexMessage['type'] = 'flex'
        flexMessage['altText'] = altText
        flexMessage['contents'] = json

        # print(json)

        jsonMessage['replyToken'] = replyToken
        jsonMessage['messages'] = [flexMessage]

        self.sendJsonReplyMessage(jsonMessage)

    def sendFlexMessage(self, replyToken, path, altText):
        with open(path) as f:
            jsonObject = json.load(f)
            jsonMessage = {}
            flexMessage = {}
            flexMessage['type'] = 'flex'
            flexMessage['altText'] = altText
            flexMessage['contents'] = jsonObject

            jsonMessage['replyToken'] = replyToken
            jsonMessage['messages'] = [flexMessage]

            self.sendJsonReplyMessage(jsonMessage)

    def sendFlexTeamMessage(self, replyToken, lene, felsa, audi, bacon, eric):
        with open('./team_view.json') as f:
            jsonObject = json.load(f)
            jsonObject['contents'][0]['body']['contents'][0]['text'] = felsa['displayName']
            jsonObject['contents'][0]['hero']['url'] = felsa['pictureUrl']

            jsonObject['contents'][1]['body']['contents'][0]['text'] = audi['displayName']
            jsonObject['contents'][1]['hero']['url'] = audi['pictureUrl']

            jsonObject['contents'][2]['body']['contents'][0]['text'] = lene['displayName']
            jsonObject['contents'][2]['hero']['url'] = lene['pictureUrl']

            jsonObject['contents'][3]['body']['contents'][0]['text'] = bacon['displayName']
            jsonObject['contents'][3]['hero']['url'] = bacon['pictureUrl']

            jsonObject['contents'][4]['body']['contents'][0]['text'] = eric['displayName']
            jsonObject['contents'][4]['hero']['url'] = eric['pictureUrl']

            jsonMessage = {}
            flexMessage = {}
            flexMessage['type'] = 'flex'
            flexMessage['altText'] = 'team'
            flexMessage['contents'] = jsonObject

            jsonMessage['replyToken'] = replyToken
            jsonMessage['messages'] = [flexMessage]

            self.sendJsonReplyMessage(jsonMessage)

    def sendTagMessage(self, replyToken):

        # {'message': {'id': '15080603943128', 'mention': {'mentionees': [{'index': 8, 'length': 21, 'userId': 'U7c4fa5c2166b0bef9bf48b69a4879f2f'}]}, 'text': '#test12 @EricLeKing (hMB/554) ', 'type': 'text'}, 'mode': 'active', 'replyToken': 'abb1427de71d4a4fb9f66fac50390dfc',
        # 'source': {'groupId': 'Ce15aeeeec12d3428076c3ddf5d811ac7', 'type': 'group', 'userId': 'Uf85852359e1f99af7ef93fe57c24a56f'}, 'timestamp': 1636862146654, 'type': 'message'}
        textMessage = {}
        textMessage['type'] = 'text'
        textMessage['text'] = '@EricLeKing (hMB/554) '
        textMessage['mention'] = {'mentionees': [
            {'index': 0, 'length': 21, 'userId': 'U7c4fa5c2166b0bef9bf48b69a4879f2f'}]}

        jsonMessage = {}
        jsonMessage['replyToken'] = replyToken
        # jsonMessage['mention'] = {'mentionees': [{'index': 1, 'length': 21, 'userId': 'U7c4fa5c2166b0bef9bf48b69a4879f2f'}]}
        jsonMessage['messages'] = [textMessage]

        print(jsonMessage)
        self.sendJsonReplyMessage(jsonMessage)

    def sendReminderCalender(self, replyToken, reminders, currentGt):
        with open('./calender_view.json') as f:
            jsonObject = json.load(f)
            jsonObject['header']['contents'][0]['contents'][1]['text'] = str(
                currentGt.strftime("%d %B %Y"))
            jsonObject['footer']['contents'][0]['contents'][1]['text'] = str(
                currentGt.strftime("%H:%M"))

            for reminder in reminders:
                if (reminder):
                    elementToAdd = {
                        'type': 'box',
                        'layout': 'horizontal',
                        'contents': [
                            {
                                'type': 'box',
                                'layout': 'horizontal',
                                'contents': [
                                   {
                                       'type': 'text',
                                       'text': reminder['reminderTime'],
                                       "gravity": "center",
                                       "size": "sm"
                                   }
                                ],
                                "flex": 1,
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "filler"
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents": [],
                                        "cornerRadius": "30px",
                                        "width": "12px",
                                        "height": "12px",
                                        "borderWidth": "2px",
                                        "borderColor": "#6486E3"
                                    },
                                    {
                                        "type": "filler"
                                    }
                                ],
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": reminder['reminderMsg'],
                                "gravity": "center",
                                "flex": 4,
                                "size": "sm"
                            }
                        ],
                        "spacing": "lg",
                        "cornerRadius": "30px",
                        "margin": "xl"
                    }

                    jsonObject['body']['contents'][1]['contents'].append(
                        copy.deepcopy(elementToAdd))

            flexMessage = {}
            flexMessage['type'] = 'flex'
            flexMessage['altText'] = 'todays agenda'
            flexMessage['contents'] = jsonObject

            jsonMessage = {}
            jsonMessage['replyToken'] = replyToken
            jsonMessage['messages'] = [flexMessage]

            self.sendJsonReplyMessage(jsonMessage)

    def sendRockImageMap(self, replyToken):

        with open('./rock_view.json') as f:
            rockMessages = ['Damn, I would tap that', 'I like me some vibrant Aussie tongue', 'I would die for that tongue']
            rockMessage = random.choice(rockMessages)
            jsonObject = json.load(f)
            jsonObject['body']['contents'][2]['action']['text'] = rockMessage

            
            flexMessage = {}
            flexMessage['type'] = 'flex'
            flexMessage['altText'] = 'Rock'
            flexMessage['contents'] = jsonObject

            jsonMessage = {}
            jsonMessage['replyToken'] = replyToken
            jsonMessage['messages'] = [flexMessage]

            self.sendJsonReplyMessage(jsonMessage)


        # message = {'type': 'imagemap', 'baseUrl':'https://raw.githubusercontent.com/audi1/lssStuff/main/rock.jpg', 'altText':'Rock', 'baseSize': {'width':1040, 'height':800}}
        # message['actions'] = [{'type':'message', 'label': 'Touch me', 'area': {'x':400, 'y':400, 'width':300, 'height': 100}, 'text':rockMessage}]
        
        # jsonMessage = {}
        # jsonMessage['replyToken'] = replyToken
        # jsonMessage['messages'] = [message]

        # print(jsonMessage)
        self.sendJsonReplyMessage(jsonMessage)
