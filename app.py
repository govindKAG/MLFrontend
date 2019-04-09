import flask
import subprocess
import time          #You don't need this. Just included it so you can see the output stream.
from flask import request

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

        for line in iter(proc.stdout.readline,''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            yield str(line).strip() + '<br/>\n'
    # text/html and text/plain seem to work
    return flask.Response(inner(podname), mimetype='text/html')  

@app.route('/pods')
def pods():
    pods = subprocess.check_output("kubectl get pods --all-namespaces", shell=True)
    return  flask.Response(pods, mimetype='text/plain')
