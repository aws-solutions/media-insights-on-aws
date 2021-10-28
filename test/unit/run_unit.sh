#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest unit test suite.
#
# PRELIMINARY:
#  You must have a functioning MIE deployment. Set the required environment variables; see the testing readme for more
#  details.
#
# USAGE:
#  ./run_unit.sh $component
#
###############################################################################

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
echo "------------------------------------------------------------------------------"

if [ "$1" = "" ]; then
    echo "Invalid positional parameter. Must select dataplaneapi or workflowapi. Quitting."
    exit 1

elif [ "$1" = "dataplaneapi" ]; then
    echo "Running dataplane unit tests"
    pytest dataplaneapi/ -s -W ignore::DeprecationWarning -p no:cacheprovider --cov=../../source/dataplaneapi
    if [ $? -eq 0 ]; then
	    exit 0
    else
	    exit 1
    fi
elif [ "$1" = "workflowapi" ]; then
    echo "Running workflow unit tests"
    pytest workflowapi/ -s -W ignore::DeprecationWarning -p no:cacheprovider --cov=../../source/workflowapi
    if [ $? -eq 0 ]; then
	    exit 0
    else
	    exit 1
    fi
else
    echo "Invalid positional parameter. Quitting."
    exit 1
fi


echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV
rm -rf  __pycache__
