import flask
import json
import subprocess
import time          
import re
import shlex

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

@app.route('/build')
def buildImage():
    version           = request.args.get('version')
    github_user       = request.args.get('github-user')
    github_revsion    = request.args.get('github-revision')
    github_repo       = request.args.get('github-repo')
    docker_user       = request.args.get('docker-user')
    train_name        = request.args.get('train-name')
    docker_image_name = request.args.get('docker-image-name')

    result = subprocess.check_output(f"argo submit build.yaml -p build-push-image=true -p execute-train=false -p docker-user={docker_user} -p github-user={github_user} -p train-name={train_name} -p version={version} -p docker-image-name={docker_image_name} -p github-repo={github_repo}", shell=True)

    argo_jobs = subprocess.check_output(shlex.split('argo list'))
    argo_jobs = argo_jobs.decode('utf-8')
    #print(argo_jobs)
    argo_jobs = argo_jobs.splitlines()
    #print(argo_jobs)
    
    latest_job = argo_jobs[1].split(' ')[0]
    
    def inner(version, github_user, github_revsion, github_repo, docker_user, train_name, docker_image_name, latest_job):
        proc = subprocess.Popen(shlex.split(f'argo logs -wf {latest_job}'), shell=True, stdout=subprocess.PIPE)

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            yield ansi_escape.sub('',bytes.decode(line).strip()) + '<br/>\n'
    return flask.Response(inner(version, github_user, github_revsion, github_repo, docker_user, train_name, docker_image_name, latest_job), mimetype='text/html')  
