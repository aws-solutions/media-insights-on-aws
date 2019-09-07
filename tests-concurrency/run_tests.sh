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
export REGION='us-west-2'
export MIE_STACK_NAME="mieor"
export TEST="test_concurrency.py"
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
# FIXME - these should be inputs to the test script
export BUCKET_NAME="burkleaa-files"
export IMAGE_FILENAME="test-media/sample-image.jpg"
export VIDEO_FILENAME="test-media/sample-video.mp4"
export VIDEO_WITH_AUDIO_FILENAME="test-media/polly_example.mp4"
export AUDIO_FILENAME="test-media/sample-audio.m4a"
export TEXT_FILENAME="test-media/sample-text.txt"


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
