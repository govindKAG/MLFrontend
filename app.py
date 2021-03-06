import flask
import json
import subprocess
import time          
import re
import shlex
import copy

from flask import request
from flask import redirect
from flask import url_for
from flask import send_file
from flask import render_template
from json2html import *
from forms import BuildForm
from forms import TrainForm
from forms import DeployForm
from forms import DemoForm
from util import generate_yaml
from util import get_train_pod_name

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'horses-batteries-salt-apples'

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

@app.route('/')
def home():
    return render_template('test.html')

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

@app.route('/list_train_pods')
def list_train_pods():
    pods = subprocess.check_output(f"kubectl get pods -l use=trainpod -o json",
            shell = True)
    pods = json.loads(pods)
    items = pods['items']
    statuses = {i['metadata']['labels']['job-name']:{ 'status':i['status']['phase'], 'command':' '.join(i['spec']['containers'][0]['command']),'args':' '.join(i['spec']['containers'][0]['args'])} for i in items}
    #return json.dumps(statuses)
    return render_template('tables.html', statuses=statuses)
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
@app.route('/trainlog/<train_name>')
def trainlog(train_name):
    train_pod_name = get_train_pod_name(train_name)
    def inner(train_pod_name):
        proc = subprocess.Popen(shlex.split(f'kubectl logs -f {train_pod_name}'), shell=True, stdout=subprocess.PIPE)
        #yield f'<h1> logs for {train_pod_name}</h1>\n'

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            yield '<p style="color: blue; line-height:2.5px; word-wrap: break-word;" >'+ansi_escape.sub('',bytes.decode(line).strip()) + '</p>\n'
    return flask.Response(inner(train_pod_name), mimetype='text/html')  

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
    github_user       = request.args.get('github_user')
    github_revsion    = request.args.get('github_revision')
    github_repo       = request.args.get('github_repo')
    docker_user       = request.args.get('docker_user')
    train_name        = request.args.get('train_name')
    docker_image_name = request.args.get('docker_image_name')

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

@app.route('/buildui', methods=['GET', 'POST'])
def buildui():
    form = BuildForm()
    if form.validate_on_submit():
        #print(request.form.to_dict())
        args = copy.deepcopy(request.form.to_dict())
        del args['csrf_token']
        return redirect(url_for('buildImage',**args))
    return render_template('build.html', title='nexo', form=form)

@app.route('/trainui', methods=['GET', 'POST'])
def trainui():
    form = TrainForm()
    if form.validate_on_submit():
        print(request.form.to_dict())
        args = copy.deepcopy(request.form.to_dict())
        del args['csrf_token']
        print(args['args'])
        generate_yaml('train.yaml', 'test.yaml', args)
        return redirect(url_for('trainImage',**args))
    return render_template('train.html', title='nexo', form=form)


@app.route('/train')
def trainImage():
    version           = request.args.get('version')
    docker_user       = request.args.get('docker_user')
    train_name        = request.args.get('train_name')
    docker_image_name = request.args.get('docker_image_name')

    result = subprocess.check_output(f"argo submit test.yaml -p build-push-image=false -p execute-train=true -p docker-user={docker_user} -p train-name={train_name} -p version={version} -p docker-image-name={docker_image_name}", shell=True)

    print(result)
    train_pod_name = get_train_pod_name(train_name)
    print(train_pod_name)
    
    def inner(version, docker_user, train_name, docker_image_name, train_pod_name):
        proc = subprocess.Popen(shlex.split(f'kubectl logs -f {train_pod_name}'), shell=True, stdout=subprocess.PIPE)

        for line in iter(proc.stdout.readline, b''):
            time.sleep(0.1)                           # Don't need this just shows the text streaming
            yield ansi_escape.sub('',bytes.decode(line).strip()) + '<br/>\n'
    return flask.Response(inner(version, docker_user, train_name, docker_image_name, train_pod_name), mimetype='text/html')  

@app.route('/deployui', methods=['GET', 'POST'])
def deployui():
    form = DeployForm()
    if form.validate_on_submit():
        #print(request.form.to_dict())
        args = copy.deepcopy(request.form.to_dict())
        del args['csrf_token']
        return redirect(url_for('deployImage',**args))
    return render_template('deploy.html', title='nexo', form=form)

@app.route('/deploy')
def deployImage():
    version           = request.args.get('version')
    github_user       = request.args.get('github_user')
    github_revsion    = request.args.get('github_revision')
    github_repo       = request.args.get('github_repo')
    docker_user       = request.args.get('docker_user')
    model_name        = request.args.get('model_name')
    docker_image_name = request.args.get('docker_image_name')

    #result = subprocess.check_output(f"argo submit serve.yaml  -p docker-user={docker_user} -p github-user={github_user} -p model-name={model_name} -p version={version} -p docker-image-name={docker_image_name} -p github-repo={github_repo}", shell=True)
    return redirect(url_for('list_models'))

    #argo_jobs = subprocess.check_output(shlex.split('argo list'))
    #argo_jobs = argo_jobs.decode('utf-8')
    ##print(argo_jobs)
    #argo_jobs = argo_jobs.splitlines()
    ##print(argo_jobs)
    #
    #latest_job = argo_jobs[1].split(' ')[0]
    #
    #def inner(version, github_user, github_revsion, github_repo, docker_user, model_name, docker_image_name, latest_job):
    #    proc = subprocess.Popen(shlex.split(f'argo logs -wf {latest_job}'), shell=True, stdout=subprocess.PIPE)

    #    for line in iter(proc.stdout.readline, b''):
    #        time.sleep(0.1)                           # Don't need this just shows the text streaming
    #        yield ansi_escape.sub('',bytes.decode(line).strip()) + '<br/>\n'
    #return flask.Response(inner(version, github_user, github_revsion, github_repo, docker_user, model_name, docker_image_name, latest_job), mimetype='text/html')  

@app.route('/list_models')
def list_models():
    sdeps     = subprocess.check_output(f"kubectl get sdep -o json",
                                       shell = True)
    sdeps     = json.loads(sdeps)
    items     = sdeps['items']
    statuses  = {i['metadata']['name']:{ 'status':i['status']['state']} for i in items}
    #return json.dumps(statuses)
    return render_template('deploytables.html', statuses=statuses)
    #return  flask.Response(pods, mimetype='text/plain')

@app.route('/demo_app')
def demo_app():
    query    = request.args.get('query')
    result   = subprocess.check_output('''curl -X POST -H "Content-Type: application/json" -d "{\\"data\\":{\\"ndarray\\":[[\\"'''+query+ '''}\\"]]}}" http://10.71.3.3:32389/seldon/emote-classifier/api/v0.1/predictions ''',shell = True)
    result   = json.loads(result)
    emotion  = 'positive'
    color    = 'bg-green'
    if result['data']['ndarray'][0][0] == 'pos':
        emotion = 'positive'
    else :
        emotion = 'negative'
        color   = 'bg-red'
    return render_template('emotion.html', color = color)
    #return render_template('deploytables.html', statuses=statuses)
    #return  flask.Response(pods, mimetype='text/plain')

@app.route('/demoui', methods=['GET', 'POST'])
def demoui():
    form = DemoForm()
    if form.validate_on_submit():
        #print(request.form.to_dict())
        args = copy.deepcopy(request.form.to_dict())
        del args['csrf_token']
        return redirect(url_for('demo_app',**args))
    return render_template('demo.html', title='nexo', form=form)
