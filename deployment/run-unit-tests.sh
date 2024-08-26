#!/bin/bash

# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh

source "$(dirname "${BASH_SOURCE[0]}")/nltk_download_functions.sh"

# Run unit tests
echo "Running unit tests"

echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing CDK"
echo "------------------------------------------------------------------------------"
chmod +x ../source/cdk/run-tests.sh && ../source/cdk/run-tests.sh || exit $?


build_dir="$(dirname "${BASH_SOURCE[0]}")"
source_dir="$build_dir/../source"

download_punkt "$source_dir"

echo "pushd ../test/unit"
pushd ../test/unit
echo "------------------------------------------------------------------------------"
echo "Installing Dependencies And Testing Modules"
echo "------------------------------------------------------------------------------"
./run_unit.sh

if [ $? -ne 0 ]; then
    echo "ERROR: Unit test script failed"
    exit 1
fi

echo "popd"
popd
cleanup_punkt "$source_dir"