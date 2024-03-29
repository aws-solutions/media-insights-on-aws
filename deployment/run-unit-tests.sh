#!/bin/bash

# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh

# Run unit tests
echo "Running unit tests"

echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing CDK"
echo "------------------------------------------------------------------------------"
chmod +x ../source/cdk/run-tests.sh && ../source/cdk/run-tests.sh || exit $?

echo "cd ../test/unit"
cd ../test/unit
echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing Modules"
echo "------------------------------------------------------------------------------"
./run_unit.sh
