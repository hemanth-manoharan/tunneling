from flask import Flask
from flask import jsonify
from flask import request

app = Flask (__name__)

@app.route('/hello',methods=['POST'])
def hello():
  response = {
    'greeting': 'Hello ' + request.json['name']
  }
  return jsonify(response)