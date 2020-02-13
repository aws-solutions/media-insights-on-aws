#!/bin/bash

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest regression test suite.
#
# PRELIMINARY:
#  You must have a functioning MIE deployment. The `./deploy.sh` script may
#  help you do that easily.
#
# USAGE:
#  ./run_tests.sh
#
###############################################################################
# User-defined environment variables
# User-defined environment variables

echo "What region is your MIE Stack in?"
read region
export REGION=$region

echo "What is the name of your MIE Stack?"
read stackname
export MIE_STACK_NAME=$stackname

echo "Enter your MIE Admin Username"
read username
export MIE_USERNAME=$username

read -p "Enter your password (enter temp password if your account is unverified)" -s password
export MIE_PASSWORD=$password

# Retrieve exports from mie stack
export BUCKET_NAME=`aws cloudformation list-stack-resources --profile default --stack-name $MIE_STACK_NAME --region $REGION --output text --query 'StackResourceSummaries[?LogicalResourceId == \`Dataplane\`]'.PhysicalResourceId`
export MIE_CLIENT_ID=`aws cloudformation list-stack-resources --profile default --stack-name $MIE_STACK_NAME --region $REGION --output text --query 'StackResourceSummaries[?LogicalResourceId == \`MieAdminClient\`]'.PhysicalResourceId`
export MIE_POOL_ID=`aws cloudformation list-stack-resources --profile default --stack-name $MIE_STACK_NAME --region $REGION --output text --query 'StackResourceSummaries[?LogicalResourceId == \`MieUserPool\`]'.PhysicalResourceId`

#################### Nothing for users to change below here ####################
# Create and activate a temporary Python environment for this script.
echo "------------------------------------------------------------------------------"
echo "Creating a temporary Python virtualenv for this script"
echo "------------------------------------------------------------------------------"
python -c "import os; print (os.getenv('VIRTUAL_ENV'))" | grep -q None
if [ $? -ne 0 ]; then
    echo "ERROR: Do not run this script inside Virtualenv. Type \`deactivate\` and run again.";
    exit 1;
fi
which python3
if [ $? -ne 0 ]; then
    echo "ERROR: install Python3 before running this script"
    exit 1
fi
VENV=$(mktemp -d)
python3 -m venv $VENV
source $VENV/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install required Python libraries."
    exit 1
fi

# Authenticate with Cognito
token=$(python3 './getAccessToken.py')
if [ $? -eq 0 ]; then
    export MIE_ACCESS_TOKEN=$token
else
    echo "ERROR: Unable to authenticate";
    exit 1;
fi

echo "------------------------------------------------------------------------------"
echo "Setup test environment variables"

export SAMPLE_IMAGE="test-media/sample-image.jpg"
export SAMPLE_VIDEO="test-media/sample-video.mp4"
export SAMPLE_AUDIO="test-media/sample-audio.m4a"
export SAMPLE_TEXT="test-media/sample-text.txt"
export SAMPLE_JSON="test-media/sample-data.json"
export SAMPLE_FACE_IMAGE="test-media/sample-face.jpg"
export FACE_COLLECTION_ID="temporary_face_collection"

echo "------------------------------------------------------------------------------"
echo "Running tests"
pytest -s -W ignore::DeprecationWarning -p no:cacheprovider
#python -m py.test -s -W ignore::DeprecationWarning -p no:cacheprovider

echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV
rm -rf  __pycache__
