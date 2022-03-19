# Copyright Audi TM


from flask import Flask, request, abort, jsonify
import os
import base64
import hashlib
import hmac
import sys
from messageHandler import MessageHandler
from scout_apm.flask import ScoutApm


app = Flask(__name__)
channel_secret = os.environ.get('CHANNEL_SECRET', None)
channel_access_token = os.environ.get('CHANNEL_ACCESS_TOKEN', None)

ScoutApm(app)


messageHandler = MessageHandler()

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

@app.route("/health", methods=['GET'])
def healthCheck():
    doStuffOnHealthCall()
    return 'OK'

    
def doStuffOnHealthCall():
    messageHandler.notifyReminder()
    

@app.route("/webhook", methods=['POST'])
def webhook():
    app.logger.info("callback received")
    signature = request.headers['X-Line-Signature']
    if signature is None:
        signature = request.headers['x-line-signature']

    body = jsonify(request.json)

    if (body.json['events'][0]['type'] == "message"):
        if (not verifySignature(request.get_data(as_text=True), signature)):
            app.logger.warning("signature validation failed")
            abort(400) 

        handle_messages(body.json)
    
    elif (body.json['events'][0]['type'] == "postback"):
        if (not verifySignature(request.get_data(as_text=True), signature)):
            app.logger.warning("signature validation failed")
            abort(400) 
        
        handle_postback(body.json)

    elif (body.json['events'][0]['type'] in ['join', 'memberJoined']):
        if (not verifySignature(request.get_data(as_text=True), signature)):
            app.logger.warning("signature validation failed")
            abort(400) 
        
        messageHandler.sendWelcomeMessage(body.json)
    
    return 'OK'
        

def handle_postback(message):
    app.logger.debug(message)
    messageHandler.handlePostback(message)

def handle_messages(message):
    app.logger.debug(message)
    messageHandler.handleMessage(message)


def verifySignature(body, request_signature):
    hash = hmac.new(channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).strip()
    return (str(signature)[2:-1] == str(request_signature))


if __name__ == "__main__":
    app.run()