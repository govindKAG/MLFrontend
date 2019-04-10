import flask
import json
import subprocess
import time          

from flask import request
from json2html import *

app = flask.Flask(__name__)

@app.route('/log')
def index():
    podname = request.args.get('podname')
    def inner(podname):
        proc = subprocess.Popen(
            ['argo','logs','-w',podname],             #call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            yield bytes.decode(line).strip() + '<br/>\n'
    # text/html and text/plain seem to work
    return flask.Response(inner(podname), mimetype='text/html')  

@app.route('/pods/<podname>')
def pods(podname):
    pods = subprocess.check_output(f"kubectl get pod {podname} -o json", shell=True)
    pods = json.loads(pods)
    output = json2html.convert(json = pods)
    return output
    #return  flask.Response(pods, mimetype='text/plain')
