import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """If you were hiring somebody at work, you'd look at applicants CVs, right?
              So why don't you look at your MP's CV?"""


