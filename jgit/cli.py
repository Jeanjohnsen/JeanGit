import argparse
import os
import sys
from . import data

def main ():
    args = parse_args()
    args.func(args)
    
def parse_args():
    parser = argparse.ArgumentParser()
    
    commands = parser.add_subparsers(dest='command')
    commands.required = True
    
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(function=init)
    
    hash_object_parser = commands.add_parser('hash_parser')
    hash_object_parser.set_defaults(function=hash_object)
    hash_object_parser.add_argument('file')
    
    cat_file_parser = commands.add_parser('cat_file')
    cat_file_parser.set_defaults(function=cat_file)
    cat_file_parser.add_argument('object')
    
    return parser.parse_args()
    
def hash_object(args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))
        
def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected = None))

def init(args):
    data.init()
    print(f'Initilized empty ugit repository in {os.getcwd}/{data.GIT_DIR}')