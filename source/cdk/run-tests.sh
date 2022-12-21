#!/usr/bin/env bash
#
# This script runs tests for the root CDK project.

# The cdk directory is the directory containing this script
cdk_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)"
cd "${cdk_dir}"

prepare_jest_coverage_report() {
    local component_name=$1

    if [ ! -d "coverage" ]; then
        echo "ValidationError: Missing required directory coverage after running unit tests"
        exit 129
    fi

    # prepare coverage reports
    rm -fr coverage/lcov-report
    mkdir -p $coverage_reports_top_path/jest
    coverage_report_path=$coverage_reports_top_path/jest/$component_name
    rm -fr $coverage_report_path
    mv coverage $coverage_report_path
}

run_cdk_project_test() {
    local component_path="$1"
    local component_name=solutions-constructs

    echo "------------------------------------------------------------------------------"
    echo "[Test] $component_name"
    echo "------------------------------------------------------------------------------"
    cd "$component_path"

    # install and build for unit testing
    npm install

    # run unit tests
    npm run test

    # prepare coverage reports
    prepare_jest_coverage_report $component_name
}

# Run unit tests
echo "Running unit tests"

# Get reference for source folder
slnroot_dir="$(dirname "$(dirname "$cdk_dir")")"
coverage_reports_top_path="$slnroot_dir/coverage-reports"

# Test the CDK project
run_cdk_project_test "$cdk_dir"
