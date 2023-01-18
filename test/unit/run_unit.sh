#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script runs our pytest unit test suite.
#
# PRELIMINARY:
#  You must have a functioning MI deployment. Set the required environment variables; see the testing readme for more
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
echo "------------------------------------------------------------------------------"

source_dir=`echo $PWD | sed "s/\/test\/unit//"`
if [ "$1" != "" ]; then
    echo "Running $1 unit tests"
    coverage_report_path="$source_dir/coverage-reports/coverage-source-$1.xml"
    pytest "$1" -s -W ignore::DeprecationWarning -p no:cacheprovider --cov="$source_dir/source/$1" --cov-report=term-missing --cov-report=xml:$coverage_report_path
    if [ $? -eq 0 ]; then
        sed -i.orig -e "s,<source>$source_dir,<source>,g" $coverage_report_path
        rm -f $source_dir/coverage-reports/*.orig
    else
        exit 1
    fi
else
    echo "Running $1 all unit tests"
    for folder in */ ; do
        echo "Running ${folder/\//} unit tests"
        coverage_report_path="$source_dir/coverage-reports/coverage-source-${folder/\//}.xml"
        pytest "$folder" -s -W ignore::DeprecationWarning -p no:cacheprovider --cov="$source_dir/source/$folder" --cov-report=term --cov-report=xml:$coverage_report_path
        if [ $? -eq 0 ]; then
            sed -i.orig -e "s,<source>$source_dir,<source>,g" $coverage_report_path
            rm -f $source_dir/coverage-reports/*.orig
        else
            exit 1
        fi
    done
fi

echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV
rm -rf  __pycache__
