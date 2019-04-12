import flask
import json
import subprocess
import time          
import re

from flask import request
from flask import send_file
from json2html import *

app = flask.Flask(__name__)

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

@app.route('/log')
def index():
    podname = request.args.get('podname')
    def inner(podname):
        proc = subprocess.Popen(
            ['argo','logs','-wf',podname],             #call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            #ansi_escape.sub('', sometext)
            yield ansi_escape.sub('',bytes.decode(line).strip()) + '<br/>\n'
    # text/html and text/plain seem to work
    return flask.Response(inner(podname), mimetype='text/html')  

@app.route('/pods/<podname>')
def pods(podname):
    pods   = subprocess.check_output(f"kubectl get pod {podname} -o json",
            shell = True)
    pods   = json.loads(pods)
    output = json2html.convert(json                                              = pods)
    return output
    #return  flask.Response(pods, mimetype='text/plain')

@app.route("/download/<path>")
def DownloadLogFile (path = None):
    if path is None:
        return "Not found"
    try:
        return send_file(path, as_attachment=True)
    except Exception as e:
        pass

#temp, doesn't stream yet
@app.route('/trainlog/<podname>')
def trainlog(podname):
    pods   = subprocess.check_output(f"kubectl logs {podname}",
            shell = True)
    output = bytes.decode(pods)
    return flask.Response(output, mimetype='text/plain')

@app.route('/stream')
def streamTest():
    podname = request.args.get('podname')
    def inner(podname):
        proc = subprocess.Popen(
            ['kubectl','logs','-f','--tail','10',podname],             #call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            #ansi_escape.sub('', sometext)
            yield ansi_escape.sub('',bytes.decode(line).strip()) + '<br/>\n'
    # text/html and text/plain seem to work
    return flask.Response(inner(podname), mimetype='text/html')  
