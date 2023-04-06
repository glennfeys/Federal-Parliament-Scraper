# This script generates URLs for parliamentary sessions and saves them in JSON format
# It takes base_url and session numbers as input arguments
# The generated URLs are saved in the 'build' directory
# The 'static' directory is copied to the 'build' directory
# The session numbers and their corresponding URLs are saved in 'index.json'

#!/usr/bin/env python3
from parliament_parser import ParliamentarySession # Importing the ParliamentarySession class from parliament_parser module
import os # Importing the os module
import sys # Importing the sys module
import json # Importing the json module
from os import path, makedirs # Importing specific functions from the os module
from distutils.dir_util import copy_tree # Importing the copy_tree function from the distutils.dir_util module

OUTPUT_PATH = "build" # Setting the output directory name as 'build'
STATIC_SITE_PATH = "static" # Setting the static directory name as 'static'

# A function to generate URL for a given session number
def session_to_URL(session):
    session = int(session) # Converting the session number to integer
    parliamentary_session = ParliamentarySession(session) # Creating an instance of the ParliamentarySession class with the given session number
    return parliamentary_session.dump_json(OUTPUT_PATH, sys.argv[1]) # Generating the URL for the given session and returning it

# A function to print the usage of the script
def print_usage():
    print(f'{sys.argv[0]} <base_url> <session> <session> ...')

# The main function of the script
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage() # If the --help argument is passed, print the usage of the script and exit
    os.makedirs(OUTPUT_PATH, exist_ok=True) # Create the output directory if it doesn't exist

    # Use a single thread to prevent us being blocked during long runs
    urls = list(map(session_to_URL, sys.argv[2:])) # Generate URLs for all the sessions passed as arguments
    sessions = {value: urls[idx] for idx, value in enumerate(sys.argv[2:])} # Create a dictionary with session numbers as keys and their corresponding URLs as values

    makedirs(OUTPUT_PATH, exist_ok=True) # Create the output directory if it doesn't exist
    copy_tree("static", "build") # Copy the static directory to the output directory
    with open(path.join(OUTPUT_PATH, 'index.json'), 'w+') as fp: # Open the index.json file in write mode
        json.dump(sessions, fp, ensure_ascii='false') # Write the session numbers and their corresponding URLs to the index.json file

if __name__ == "__main__":
    main() # Call the main function if the script is run directly