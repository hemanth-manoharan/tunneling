from flask import Flask
from flask import jsonify
from flask import request

app = Flask (__name__)

@app.route('/hello',methods=['POST'])
def hello():
  response = {
    'greeting': 'Hello ' + request.json['name'],
    'method': request.method
  }
  return jsonify(response)

@app.route('/update',methods=['PUT'])
def update():
  return ('', 204)
