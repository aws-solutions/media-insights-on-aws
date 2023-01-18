#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest integration test suite.
#
# PRELIMINARY:
#  You must have a functioning MI deployment. Set the required environment variables; see the testing readme for more
#  details.
#
# USAGE:
#  ./run_integ.sh $component
#
###############################################################################
# User-defined environment variables

if [ -z REGION ]
then
    echo "You must set the AWS region your MI stack is install in under the env variable 'REGION'. Quitting."
    exit
fi

if [ -z MI_STACK_NAME ]
then
    echo "You must set the name of your MI stack under the env variable 'MI_STACK_NAME'. Quitting."
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
if [ -n "${VIRTUAL_ENV:-}" ]; then
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
export SAMPLE_IMAGE="sample-image.jpg"
export SAMPLE_TERMINOLOGY="sampleterminology"
export TEST_PARALLEL_DATA_NAME="sample_parallel_data"
export TEST_PARALLEL_DATA="sample_parallel_data.csv"

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
