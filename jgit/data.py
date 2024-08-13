import os
import hashlib

GIT_DIR = '.jgit'  # Directory name used to store the repository objects

    # Initializes a new repository by creating the necessary directories.
    # Creates the '.jgit' directory and a subdirectory 'objects' to store all objects.
def init():
    os.makedirs(GIT_DIR)
    os.makedirs(f'{GIT_DIR}/objects')
   
    
    # Creates a new object by hashing the provided data with a specified type.
    # The type (default is 'blob') is prepended to the data, and the combined content is hashed.
    # The resulting hash (OID) is then used to store the object in the '.jgit/objects' directory.
def hash_object(data, type_='blob'):
    obj = type_.encode() + b'\x00' + data  # Create the object content with type and data
    oid = hashlib.sha1(obj).hexdigest()  # Generate the SHA-1 hash (object ID)
    
    # Save the object content to a file named after its OID in the objects directory
    with open(f'{GIT_DIR}/objects/{oid}', 'wb') as out:
        out.write(obj)
    return oid  # Return the object ID (OID)

    # Retrieves and returns the content of an object given its OID.
    # The object is read from the '.jgit/objects' directory and validated against the expected type.
def get_object(oid, expected='blob'):
    with open(f'{GIT_DIR}/objects/{oid}', 'rb') as f:
        obj = f.read()  # Read the raw object content from the file
        
    type_, _, content = obj.partition(b'\x00')  # Split the object into type and content
    type_ = type_.decode()  # Decode the type from bytes to string
    
    # If an expected type is provided, ensure the object's type matches the expected type
    if expected is not None:
        assert type_ == expected, f'Expected {expected}, got {type_}'
    return content  # Return the object content (excluding the type header)
