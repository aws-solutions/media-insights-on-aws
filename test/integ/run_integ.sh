#!/bin/bash

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest integration test suite.
#
# PRELIMINARY:
#  You must have a functioning MIE deployment. Set the required environment variables; see the testing readme for more
#  details.
#
# USAGE:
#  ./run_integ.sh $component
#
###############################################################################
# User-defined environment variables

if [ -z MIE_REGION ]
then
    echo "You must set the AWS region your MIE stack is install in under the env variable 'MIE_REGION'. Quitting."
    exit
fi

if [ -z MIE_STACK_NAME ]
then
    echo "You must set the name of your MIE stack under the env variable 'MIE_STACK_NAME'. Quitting."
    exit
fi

if [ -z AWS_ACCESS_KEY_ID ]
then
    echo "You must set the env variable 'AWS_ACCESS_KEY_ID' with a valid IAM access key id. Quitting."
    exit
fi

if [ -z AWS_SECRET_ACCESS_KEY ]
then
    echo "You must set the env variable 'AWS_SECRET_ACCESS_KEY' with a valid IAM secret access key. Quitting."
    exit
fi

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
echo "------------------------------------------------------------------------------"
echo "Setup test environment variables"

export TEST_MEDIA_PATH="../test-media/"
export TEST_IMAGE="sample-image.jpg"
export TEST_VIDEO="sample-video.mp4"
export TEST_AUDIO="sample-audio.m4a"
export TEST_TEXT="sample-text.txt"
export TEST_JSON="sample-data.json"
export TEST_FACE_IMAGE="sample-face.jpg"
export TEST_FACE_COLLECTION_ID="temporary_face_collection"

# Retrieve exports from mie stack
#export BUCKET_NAME=`aws cloudformation list-stack-resources --profile default --stack-name $MIE_STACK_NAME --region $REGION --output text --query 'StackResourceSummaries[?LogicalResourceId == \`Dataplane\`]'.PhysicalResourceId`

echo "------------------------------------------------------------------------------"
if [ "$1" = "" ]; then
    echo "Running all integ tests"
    pytest -s -W ignore::DeprecationWarning -p no:cacheproviders
    if [ $? -eq 0 ]; then
	exit 0
    else
	exit 1
    fi
elif [ "$1" = "dataplaneapi" ]; then
    echo "Running dataplane integ tests"
    pytest dataplaneapi/ -s -W ignore::DeprecationWarning -p no:cacheprovider
    if [ $? -eq 0 ]; then
	exit 0
    else
	exit 1
    fi
elif [ "$1" = "workflowapi" ]; then
    echo "Running workflow integ tests"
    pytest workflowapi/ -s -W ignore::DeprecationWarning -p no:cacheprovider
    if [ $? -eq 0 ]; then
	exit 0
    else
	exit 1
    fi
else
    echo "Invalid positional parameter. Quitting."
    exit
fi


echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV
rm -rf  __pycache__
