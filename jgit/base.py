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
    tree = ''.join(
                f'{type_} {oid} {name}\n'
                for name, oid, type_
                in sorted(entries)
                )
    return data.hash_object(tree.encode(), 'tree')  # Hash the tree object and return its object ID
    
 
 # iter_tree_entries is a generator that will take an OID of a tree, 
 # tokenize it line-by-line and yield the raw string values.
def iter_tree_entries(oid):
    
    if not oid:
        return
    
    tree = data.get_object(oid, 'tree')
    
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(' ', 2)
        yield type_, oid, name
    
    
        
 # Recursively retrieves all the files and subdirectories within a tree object.
 # Returns a dictionary where keys are file/directory paths and values are their corresponding object IDs.
def get_tree(oid, base_path = ''):
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
    
    empty_current_directory() # Make sure to empty the current dir on read_tree
    
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)  # Create the directory if it doesn't exist
        with open(path, 'wb') as f:  # Open the file in binary write mode
            f.write(data.get_object(oid))  # Write the content of the object (blob) to the file
    

    # Recursively deletes all files and directories in the current directory,
    # except for those that are ignored or cannot be removed.
def empty_current_directory():
    
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
    
    # Determines if a path should be ignored by checking if it contains '.jgit'
    # (i.e., it belongs to the .jgit directory used by this VCS).
def is_ignored(path):
    return '.jgit' in path.split('/')