from flask import Flask, request
import config
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("Data received from Webhook is: ", request.json)
        return "Webhook received!"

app.run(host=config.WEBHOOK_IP, port=WEBHOOK_PORT)