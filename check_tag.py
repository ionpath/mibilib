"""
This file contains functions that checks if tag in git and in
setup.py are same. If they are not an exception is raised.
"""

import re
import subprocess


def check_tag():
    """
    This function checks if tag in git and in setup.py are same and
    returns a boolean
    """
    setuppy_version = get_tag_in_setuppy("setup.py")
    tag_version = get_latest_tag()
    print("The version number in setup.py is : ", setuppy_version)
    print("The version number in git tag is : ", tag_version)
    return setuppy_version == tag_version

def get_latest_tag():
    """
    This function gets the tag from git and formats it as a string
    for later use.
    """
    proc = subprocess.Popen(["git", "describe", "--tag"],\
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = proc.communicate()
    version = stdout.strip().decode('utf-8')
    pattern = r"v(\d+).(\d+).(\d+)(.*?)"
    match = re.match(pattern, version)
    if match:
        major = match.group(1)
        minor = match.group(2)
        build = match.group(3)
        return "v"+".".join((major, minor, build))
    return ""

def get_tag_in_setuppy(file_path):
    """
    This function gets the tag from setup.py and formats it as a
    string for later use.
    """
    pattern = r"version='(\d+).(\d+).(\d+)',"
    with open(file_path) as fo:
        for line in fo:
            if line.strip().startswith("version"):
                match = re.match(pattern, line.strip())
                if match:
                    major = match.group(1)
                    minor = match.group(2)
                    build = match.group(3)
                    return "v"+".".join((major, minor, build))
    return ""

if __name__ == '__main__':
    if not check_tag():
        raise \
            Exception("The version number in setup.py and git tag do not match")
