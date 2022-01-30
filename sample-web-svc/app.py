from flask import Flask
from flask import jsonify
from flask import request

app = Flask (__name__)

@app.route('/greetings',methods=['POST'])
def greet():
  response = {
    'greeting': 'Hello ' + request.json['name']
  }
  return jsonify(response)

@app.route('/greetings/<greetingId>',methods=['GET'])
def retrieve(greetingId):
  response = {
    'greeting': 'Greeting #' + greetingId
  }
  return jsonify(response)

@app.route('/greetings/<greetingId>',methods=['PUT'])
def update(greetingId):
  return ('', 204)

@app.route('/greetings/<greetingId>',methods=['DELETE'])
def delete(greetingId):
  return ('', 204) 
