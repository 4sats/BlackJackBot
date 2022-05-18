from flask import Flask, request, Response
import json

app = Flask(__name__)

@app.route('/',methods=['POST'])
def foo():
   #data = json.loads(request.data)
   print(str(request.data))
   return Response(status=200)

if __name__ == '__main__':
   app.run()