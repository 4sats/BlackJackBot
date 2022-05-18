from flask import Flask, request, Response
import json
import sys
import logging

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
   #data = json.loads(request.data)
   logging.debug('This: '+ str(request.data))
   return Response(status=200)

if __name__ == '__main__':
   logging.basicConfig(filename='f.log', encoding='utf-8', level=logging.DEBUG)
   app.run()