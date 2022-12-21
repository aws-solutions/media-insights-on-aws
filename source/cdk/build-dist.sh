#!/usr/bin/env bash
###############################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# PURPOSE:
#   Export cloud formation templates from the API projects using chalice
#
# USAGE:
#  ./build-dist.sh
#
###############################################################################



# The cdk directory is the directory containing this script
cdk_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)"
# The source directory is the parent of the cdk directory
source_dir="$(dirname "$cdk_dir")"

# Create and activate a temporary Python environment for this script.
if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo "ERROR: Do not run this script inside Virtualenv. Type \`deactivate\` and run again." >&2
    exit 1
fi
if ! command -v python3 &>/dev/null; then
    echo "ERROR: install Python3 before running this script" >&2
    exit 1
fi
VENV="$(mktemp -d)" && echo "Using virtual python environment: $VENV"
python3 -m venv "$VENV"
source "${VENV}/bin/activate"

trap trap_error INT TERM ERR EXIT

trap_error() {
  echo "It's a trap!"
  cleanup
  exit 1
}

cleanup() {
  trap - INT TERM ERR EXIT
  # Deactivate and remove the temporary python virtualenv used to run this script
  if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo "Removing $VENV"
    [ -n "$VENV" ] && rm -rf "$VENV"
  fi
}

pip3 install wheel
pip3 install --quiet boto3 chalice docopt pyyaml jsonschema aws_xray_sdk
export PYTHONPATH="$PYTHONPATH:$source_dir/lib/MediaInsightsEngineLambdaHelper/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install required Python libraries." >&2
    exit 1
fi

if ! [ -x "$(command -v chalice)" ]; then
  echo 'Chalice is not installed. It is required for this solution. Exiting.' >&2
  exit 1
fi

# Workflow API

echo "Building Workflow API Stack"
cd "$source_dir/workflowapi" || exit 1
[ -e dist ] && rm -rf dist
mkdir -p dist

# Remove chalice deployments to force redeploy when there are changes to configuration only
# Otherwise, chalice will use the existing deployment package
[ -e .chalice/deployments ] && rm -rf .chalice/deployments

echo "running chalice..."
chalice package dist || exit 1
echo "...chalice done"

mkdir -p "$cdk_dir/dist"
cp dist/sam.json "$cdk_dir/dist/media-insights-workflow-api-stack.template"
rm -rf ./dist


# Dataplane API

echo "Building Dataplane API Stack"
cd "$source_dir/dataplaneapi" || exit 1
[ -e dist ] && rm -rf dist
mkdir -p dist

# Remove chalice deployments to force redeploy when there are changes to configuration only
# Otherwise, chalice will use the existing deployment package
[ -e .chalice/deployments ] && rm -rf .chalice/deployments

echo "running chalice..."
chalice package dist || exit 1
echo "...chalice done"

mkdir -p "$cdk_dir/dist"
cp dist/sam.json "$cdk_dir/dist/media-insights-dataplane-api-stack.template"
rm -rf ./dist


# Clean up

cleanup
exit 0
