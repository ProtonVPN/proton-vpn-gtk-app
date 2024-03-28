#!/usr/bin/env python
'''
This program validates the versions.yml. It validates:
- The file is valid yml
- That all necesary fields are in the file.
- That all the fields in the file are correctly formatted and are the correct types.
'''
import os
import yaml
import versions

ROOT = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))
)
VERSIONS = os.path.join(ROOT, "versions.yml")

def validate():
    '''
    Validates the versions.yml in this repo.
    '''
    with open(VERSIONS, encoding="utf-8") as versions_file:
        versions_yml = list(yaml.safe_load_all(versions_file))
        versions.validate_versions(versions_yml)

if __name__ == "__main__":
    validate()
