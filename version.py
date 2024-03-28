'''
This file has the logic to read the latest version from
the versions.yml file.
'''
import os
import re

VERSIONS = "versions.yml"

def read_from_versions():
    '''
    This reads the last version from the changelog.yml file.
    '''

    # This is how the first line of the changelog.yml should look
    re_version = re.compile("version: ([a-zA-Z0-9.~]+)")

    # Work out where the changelog.yml file is
    root_directory = os.path.dirname(os.path.realpath(__file__))
    versions_path = os.path.join(root_directory, VERSIONS)

    # Open the changelog file for reading.
    with open(versions_path, encoding="utf-8") as changelog:

        # Read the first line
        first_line = changelog.readline()

        # Check it matches the regex and pull out the version
        # from it.
        version_elems = re_version.match(first_line)
        if not version_elems:
            raise Exception(
                f"Cant get version from first line of changelog. '{first_line}'"
            )

        return version_elems.groups()[0]