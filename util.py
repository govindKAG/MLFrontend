import shlex
import subprocess
import time
from ruamel.yaml import YAML 

def generate_yaml(input_file_name, output_file_name, args):
    yaml = YAML()
    yaml.preserve_quotes = True
    arglist  = []
    command = args['command']
    arguments = args['args']
    arglist.append(shlex.split(command.strip()))
    for i in arguments.split():
        arglist.append(i.strip().split(':'))
    command_str = [ '"' + i +'"' for i in arglist.pop(0)]
    command_str = '[' + ','.join(command_str) + ']'
    transformed = ['"--' +str(i[0]) + '=' + str(i[1]) + '"'  for i in arglist]
    tranformed_str = '['+','.join(transformed) + ']'
    print(command_str, tranformed_str, sep='\n')
    with open(f'{input_file_name}', 'r') as f:
        ogfile = yaml.load(f)

    ogfile['spec']['templates'][2]['resource']['manifest'] = ogfile['spec']['templates'][2]['resource']['manifest'].format(command=command_str, args=tranformed_str)
    
    
    with open(f"{output_file_name}", "w") as f:
        #yaml.dump(ogfile, f, default_flow_style=False)
        yaml.dump(ogfile, f) 

def get_train_pod_name(job_name):
    time.sleep(5)
    output = subprocess.check_output("kubectl get pods", shell=True)
    output = bytes.decode(output)
    print(output)
    for i in output.split():
        if job_name in i:
            print(i)
            return i

#if __name__ == '__main__':
#    get_train_pod_name('emote-trainb17')
