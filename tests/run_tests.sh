#!/bin/bash
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest regression test suite.
#
# PRELIMINARY:
#   You must have a functioning MIE deployment. The `./deploy.sh` script may
#   help you do that easily.
#
# USAGE:
#   Set the REGION and MIE_STACK_NAME env variables to the region and stack
#   that you've already deployed and want to test. Then run `./run_tests.sh`.
#
###############################################################################
# Test environment variables
export REGION='us-east-1'
export MIE_STACK_NAME="mie"
export BUCKET_NAME="mie-testing-bucket-"$(date +%s)
export TEST="test_operation_crud.py"
export MIE_CLIENT_ID=''
export MIE_POOL_ID=''

echo "Enter your MIE Username"
read username
export MIE_USERNAME=$username
echo "Enter your MIE Password"
read password
export MIE_PASSWORD=$password

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
echo "Running tests"
pytest -s -W ignore::DeprecationWarning -p no:cacheprovider -c pytest.ini

echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV
rm -rf  __pycache__
