#!/bin/bash

# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh

# Run unit tests
echo "Running unit tests"

echo "cd ../test/unit"
cd ../test/unit
echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing WorkflowApi"
echo "------------------------------------------------------------------------------"
./run_unit.sh workflowapi


echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing DataplaneApi"
echo "------------------------------------------------------------------------------"
./run_unit.sh dataplaneapi
