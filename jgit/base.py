import os

from . import data

    # Recursively creates a tree object for the directory structure.
    # Iterates over all entries in the specified directory, generating
def write_tree(directory='.'):
   
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
    tree = ''.join(f'{type_} {oid} {name}\n'
                   for name, oid, type_
                   in sorted(entries))
    return data.hash_object(tree.encode(), 'tree')  # Hash the tree object and return its object ID
    
    
    # Determines if a path should be ignored by checking if it contains '.jgit'
    # (i.e., it belongs to the .jgit directory used by this VCS).
def is_ignored(path):
    return '.jgit' in path.split('/')