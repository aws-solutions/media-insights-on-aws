#!/usr/bin/env python3

# # Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Convert SAM templates to CloudFormation templates.
Known limitations: cannot transform CodeUri pointing at local directory.
Usage:
  sam-translate.py [--input-file=sam-template.yaml] [--output-file=<o>] [--profile=<n>]

Options:
  -i FILE, --input-file=IN_FILE     Location of SAM template to transform.
  -o FILE, --output-file=OUT_FILE   Location to store resulting CloudFormation template [default: cfn-template.json].
  -p PROFILE, --profile=AWS_PROFILE Name of AWS profile saved in user's env (e.g. ~/.aws/config)
"""
import json
import os
import boto3
from docopt import docopt
import functools

from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse
from samtranslator.model.exceptions import InvalidDocumentException

iam_client = boto3.client('iam')
# Use the specified AWS profile if it was provided.
cli_options = docopt(__doc__)
if cli_options.get('--profile'):
    session = boto3.Session(profile_name=cli_options.get('--profile'))
    iam_client = session.client('iam')
cwd = os.getcwd()


def main():
    print(cwd)
    input_file_path = cwd+'/dist/sam.json'
    output_file_path = cwd+'/dist/workflowapi.json'

    print(input_file_path)

    with open(input_file_path, 'r') as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(
            sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(
            cloud_formation_template, indent=2)

        with open(output_file_path, 'w') as f:
            f.write(cloud_formation_template_prettified)

        print('Wrote transformed CloudFormation template to: ' + output_file_path)
    except InvalidDocumentException as e:
        errorMessage = functools.reduce(lambda message, error: message + ' ' + error.message, e.causes, e.message)
        print(errorMessage)
        errors = map(lambda cause: cause.message, e.causes)
        print(errors)


if __name__ == '__main__':
    main()
