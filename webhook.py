from flask import Flask, request, Response
import json
import sys

app = Flask(__name__)

@app.route('/<path:path>',methods=['POST'])
def foo(path):
   #if request.remote_addr == "165.227.164.18":
   print(path + request.remote_addr + str(request.json)+" fuck meeeeeeee", file=sys.stderr)
   #update balance
   #send message to user about it
   return Response(status=200)

if __name__ == '__main__':
   app.run()