import os
import sys
import json

import requests
from flask import Flask, request

import requests
import json



app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    flag=True
                    if ':' in message_text:
                        if 'meaning' == message_text.lower().split(':')[0]:
                            get_meaning(sender_id,message_text.lower().split(':')[1])
                    else:
                        for word in message_text.lower().split(' '):
                            if word in ['hi','hello','hey','what\'s up','sup']:
                                send_message(sender_id, "Hey there! How can I help you?")
                                flag=False
                                break
                            elif word in ['bitch','fuck','asshole','cunt']:
                                send_message(sender_id,"If you keep using cuss words, I'm gonna report you to Developers and make sure you will get kicked out of this app!")
                                flag=False
                                break
                        if flag:
                            send_message(sender_id,"Sorry didn't get that. Try again.")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def get_meaning(sender_id,word_id):
    language='en'
    #word_id='Ace'
    app_id='f07036b2'

    app_key='163aaf3ff582ab1fbe0c626c2a94685d'
    url='https://od-api.oxforddictionaries.com:443/api/v1/entries/'+language+'/'+word_id.lower()

    r=requests.get(url,headers={'app_id':app_id,'app_key':app_key})
    big_string=''
    if r.status_code==200:
        json_text=r.json()
        #print(r.text.encode('ascii','ignore'))
        #print(json_text['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions'])
        big_string=big_string+'Definitions \n\n'
        try:
            defn=json_text['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions']
            exms=json_text['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['examples']

            if defn:
                for i in range(0,len(defn)):
                    string1=str(i+1)+'. '+defn[i]
                    big_string=big_string+string1+'\n'
            else:
                big_string=big_string+'No definitions found.\n'
            big_string=big_string+'\n\n'
            big_string=big_string+'Examples: \n'
            if exms:
                for i in range(0,len(exms)):
                    string2=str(i+1)+'. '+exms[i]['text'].encode('ascii','ignore')
                    big_string=big_string+string2+'\n'
            else:
                big_string=big_string+'No examples found\n'
        except Exception as e:
            big_string=big_string+'Sorry some error occured. Contact admin.\n'
    else:
        big_string=big_string+'Sorry couldn\'t find\n'
    send_message(sender_id,big_string)


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
