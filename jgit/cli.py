import argparse
import os
import sys
import textwrap

from . import data
from . import base

# Entry point for the script. Parses command-line arguments and executes
# the corresponding function based on the parsed arguments.
def main():
    args = parse_args()
    args.func(args)

# Sets up the argument parser for the command-line interface (CLI).
# Defines subcommands ('init', 'hash-object', 'cat_file', 'write_tree'),
# and associates each subcommand with a specific function to execute.
def parse_args():
    parser = argparse.ArgumentParser()

    # Create a subparser object to handle different subcommands
    commands = parser.add_subparsers(dest='command')
    commands.required = True  # Ensure that a command is required

    # Define the 'init' command and set the function to call as 'init'
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    # Define the 'hash-object' command and set the function to call as 'hash-object'
    # Also, add a required 'file' argument for this command
    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')

    # Define the 'cat_file' command and set the function to call as 'cat-file'
    # Also, add a required 'object' argument for this command
    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object')

    # Define the 'write_tree' command and set the function to call as
    # 'write-tree'
    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    # Define the 'read_tree' command and set the function to call as
    # 'read-tree'
    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree')

    # Define the 'commit' command and set the function to call as 'commit'
    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    # Define the 'log' command and set the function to call as 'log'
    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', nargs='?')

    # Define the 'checkout' command and set the function to call as 'checkout'
    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('oid')

    # Define the 'tag' command and set the function to call as 'tag'
    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', nargs='?')

    # Parse the command-line arguments and return the parsed arguments object
    return parser.parse_args()

# Reads the content of the specified file in binary mode,
# hashes the content using a method from the 'data' module,
# and prints the resulting hash.
def hash_object(args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))

# Ensures that stdout is flushed and then writes the binary content
# of the specified object (retrieved from the 'data' module) to stdout.
def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

# Prints the result of the 'write_tree' function from the 'base' module.
def write_tree(args):
    print(base.write_tree())

# Retrieves the file OIDs and stores them in the dictionary
def read_tree(args):
    base.read_tree(args.tree)


def commit(args):
    base.commit(args.message)


def log(args):
    oid = args.oid or data.get_ref('HEAD')

    while oid:
        commit = base.get_commit(oid)

        print(f'commmit {oid}\n')
        print(textwrap.indent(commit.message, '     '))
        print('')

        oid = commit.parent


def checkout(args):
    base.checkout(args.oid)


def tag(args):
    oid = args.oid or data.get_ref('HEAD')
    base.create_tag(args.name, oid)


# Initializes a new ugit repository using the 'init' function from the 'data' module.
# Then, prints a message indicating the initialization of the repository.
def init(args):
    print(f'Initialized empty jgit repository in {os.getcwd()}/{data.GIT_DIR}')
