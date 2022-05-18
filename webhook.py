from flask import Flask, request, Response
import json
import sys
import logging

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
   #data = json.loads(request.data)
   logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
   logging.debug('This: '+ str(request.data))
   return Response(status=200)

if __name__ == '__main__':
   app.run()