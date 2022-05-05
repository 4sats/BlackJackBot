from flask import Flask, request, Response
app = Flask(__name__)
@app.route('/', methods=['POST'])
def return_response():
    print(request.json);
    ## Do something with the request.json data.
    return Response(status=200)
if __name__ == "__main__": app.run()