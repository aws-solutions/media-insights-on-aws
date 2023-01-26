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

# Make sure working directory is the directory containing this script
cd "$(dirname "${BASH_SOURCE[0]}")"

# Make sure we clean up
cleanup_before_exit() {
    cleanup $?
}

cleanup() {
    # Reset the signals to default behavior
    trap - SIGINT SIGTERM EXIT
    echo "------------------------------------------------------------------------------"
    echo "Cleaning up"
    echo "------------------------------------------------------------------------------"

    # Deactivate and remove the temporary python virtualenv used to run this script
    deactivate
    rm -rf $VENV
    rm -rf  __pycache__
    exit ${1:-0}
}

# Create and activate a temporary Python environment for this script.

echo "------------------------------------------------------------------------------"
echo "Creating a temporary Python virtualenv for this script"
echo "------------------------------------------------------------------------------"
if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo "ERROR: Do not run this script inside Virtualenv. Type \`deactivate\` and run again.";
    exit 1;
fi
if ! command -v python3 &>/dev/null; then
    echo "ERROR: install Python3 before running this script"
    exit 1
fi
VENV=$(mktemp -d)
python3 -m venv $VENV
source $VENV/bin/activate

# Trap exits so we are sure to clean up the virtual environment
trap cleanup_before_exit SIGINT SIGTERM EXIT

# Install packages into the virtual environment
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install required Python libraries."
    exit 1
fi

echo "------------------------------------------------------------------------------"
echo "Setup test environment variables"
echo "------------------------------------------------------------------------------"

source_dir=`cd ../../source; pwd`
coverage_reports_dir="$source_dir/test/coverage-reports"

run_tests() {
    while [ $# -ne 0 ]; do
        local tc="${1%/}"
        shift

        echo "Running ${tc} unit tests"
        coverage_report_path="$coverage_reports_dir/coverage-source-${tc}.xml"
        pytest "${tc}" -s -W ignore::DeprecationWarning \
            -W 'ignore:IAMAuthorizer is not a supported in local mode:UserWarning' -p no:cacheprovider \
            --cov="$source_dir/${tc}" --cov-report=term --cov-report=xml:$coverage_report_path \
            || exit 1

        sed -i.orig -e "s,<source>$source_dir,<source>source,g" $coverage_report_path
        rm -f $coverage_reports_dir/*.orig
    done
}

if [ $# -gt 0 ]; then
    # Run all tests spcified as command line arguments
    run_tests "$@"
else
    # No tests specified so run all of them found in sub-directories
    echo "Running all unit tests"
    run_tests */
fi

cleanup $?
