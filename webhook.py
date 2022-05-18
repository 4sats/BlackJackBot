from flask import Flask, request, Response
import json
import sys

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
   print(str(request.json)+" fuck meeeeeeee", file=sys.stderr)
   return Response(status=200)

if __name__ == '__main__':
   app.run()