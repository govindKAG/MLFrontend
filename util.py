import shlex
from ruamel.yaml import YAML 

def generate_yaml(input_file_name, output_file_name, args):
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
