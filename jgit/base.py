import os
import itertools
import operator

from collections import namedtuple

from . import data

# Recursively creates a tree object for the directory structure.
# Iterates over all entries in the specified directory, generating
def write_tree(directory='.'):

    ensure_jgit_directory()
   
    # a list of (name, oid, type) tuples representing files ('blobs') and subdirectories ('trees').
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'  # Full path of the current entry
            
            if is_ignored(full):  # Skip ignored files/directories (like .jgit)
                continue
            
            if entry.is_file(follow_symlinks=False):  # If the entry is a file (not a symlink)
                type_ = 'blob'
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read(), full)  # Hash the file's content and get the object ID
            
            elif entry.is_dir(follow_symlinks=False):  # If the entry is a directory (not a symlink)
                type_ = 'tree'
                oid = write_tree(full)  # Recursively write the tree for the subdirectory
            entries.append((entry.name, oid, type_))  # Add the entry to the list
            
    # Create a tree object from the collected entries, sorted by entry name
    tree = ''.join(
                f'{type_} {oid} {name}\n'
                for name, oid, type_
                in sorted(entries)
                )
    return data.hash_object(tree.encode(), 'tree')  # Hash the tree object and return its object ID
    
 
# iter_tree_entries is a generator that will take an OID of a tree, 
# tokenize it line-by-line and yield the raw string values.
def iter_tree_entries(oid):

    ensure_jgit_directory()
    
    if not oid:
        return
    
    tree = data.get_object(oid, 'tree')
    
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(' ', 2)
        yield type_, oid, name
    
    
        
# Recursively retrieves all the files and subdirectories within a tree object.
# Returns a dictionary where keys are file/directory paths and values are their corresponding object IDs.
def get_tree(oid, base_path = ''):
    
    ensure_jgit_directory()
    
    result = {}
    
    # Iterate over entries in the tree object with the given OID
    for type_, oid, name in iter_tree_entries(oid):
        
        assert '/' not in name  # Ensure that the name does not contain a forward slash
        assert name not in ('..', '.')  # Ensure that the name is not '..' or '.'
        
        # Construct the full path of the current entry
        path = base_path + name
        if type_ == 'blob':  # If the entry is a file (blob)
            result[path] = oid  # Add the file path and its OID to the result dictionary
        elif type_ == 'tree':  # If the entry is a subdirectory (tree)
            # Recursively get the tree entries and update the result dictionary
            result.update(get_tree(oid, f'{path}/')) 
        else:
            assert False, f'Unknown tree type {type_}'  # Raise an error for unknown types
        
    return result  # Return the dictionary of paths and their corresponding OIDs
    
# Extracts the contents of a tree object and writes them to the filesystem.
# Creates the necessary directories and writes files at their respective paths.
def read_tree(tree_oid):

    ensure_jgit_directory()
    empty_current_directory() # Make sure to empty the current dir on read_tree
    
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)  # Create the directory if it doesn't exist
        with open(path, 'wb') as f:  # Open the file in binary write mode
            f.write(data.get_object(oid))  # Write the content of the object (blob) to the file
    

# Recursively deletes all files and directories in the current directory,
# except for those that are ignored or cannot be removed.
def empty_current_directory():
    
    ensure_jgit_directory()

    # Traverse the directory tree starting from the current directory,
    # walking from the deepest directories (bottom) to the top (topdown=False).
    for root, dirnames, filenames in os.walk('.', topdown=False):
        
        # Iterate over all files in the current directory
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')  # Get the relative path of the file
            if is_ignored(path) or not os.path.isfile(path):  # Skip ignored files or non-file paths
                continue
            os.remove(path)  # Remove the file
            
        # Iterate over all directories in the current directory
        for dirname in dirnames:
            path = os.path.relpath(f'{root}/{dirname}')  # Get the relative path of the directory
            if is_ignored(path) or not os.path.isfile(path):  # Skip ignored directories or non-file paths
                continue
            try:
                os.rmdir(path)  # Attempt to remove the directory (only works if it's empty)
            except (FileNotFoundError, OSError):
                # If the directory cannot be removed because it's not empty or another issue occurs, ignore the error
                pass


    #
    #
def commit(message):

    commit = f'tree {write_tree()}\n'

    HEAD = data.get_HEAD()
    if HEAD:
        commit += f'parent {HEAD}\n'

    commit += '\n'
    commit += f'{message}\n'

    oid = data.hash_object(commit.encode(), 'commit')

    data.set_HEAD(oid)

    return oid


Commit = namedtuple('Commit', ['tree', 'parent', 'message'])

def get_commit(oid):
    parent = None

    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())

    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'Unknown field {key}'

    message = '\n'.join(lines)
    return Commit(tree=tree, parent=parent, message=message)


# allows us to travel conveniently in history. 
# If we've made a handful of commits and we would like 
# to revisit a previous commit, we can now "checkout" 
# that commit to the working directory, play with it 
# (compile, run tests, read code, whatever we want) 
# and checkout the latest commit again to resume working where we've left.
def checkout(oid):
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.set_HEAD(oid)
    

def create_tag(name, oid):
    # TODO create the tag method, yeah
    pass


# Determines if a path should be ignored by checking if it contains '.jgit'
# (i.e., it belongs to the .jgit directory used by this VCS).
def is_ignored(path):
    return '.jgit' in path.split('/')


def ensure_jgit_directory():
    """
    Checks if the .jgit directory and its necessary subdirectories are created.
    If not, it creates them.
    """
    git_dir = '.jgit'
    objects_dir = f'{git_dir}/objects'
    
    # Check if .jgit directory exists
    if not os.path.isdir(git_dir):
        print(f"{git_dir} directory does not exist. Initializing the repository...")
        os.makedirs(git_dir)
        os.makedirs(objects_dir)
        print(f"{git_dir} and {objects_dir} directories have been created.")
    else:
        # Check if objects directory exists
        if not os.path.isdir(objects_dir):
            print(f"{objects_dir} directory does not exist. Creating it now...")
            os.makedirs(objects_dir)
            print(f"{objects_dir} directory has been created.")
        else:
            print(f"{git_dir} and {objects_dir} directories are already in place.")

    print("Repository structure is set up correctly.")
