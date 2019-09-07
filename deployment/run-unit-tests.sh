#!/bin/bash

# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh

# Run unit tests
echo "Running unit tests"
echo "cd ../source"
echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing Analysis"
echo "------------------------------------------------------------------------------"
cd ../source/analysis
npm install
npm test

echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing API"
echo "------------------------------------------------------------------------------"
cd ../api
npm install
npm test

echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing Helper"
echo "------------------------------------------------------------------------------"
cd ../helper
npm install
#npm test

echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing Complete"
echo "------------------------------------------------------------------------------"
