from flask import Flask, request, Response
import json
import sys
import logging

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
   #data = json.loads(request.data)
   f = open("test.txt", "a")
   f.write("Now "+ str(request.data))
   f.close()
   return Response(status=200)

if __name__ == '__main__':
   app.run()