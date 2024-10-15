#!/bin/bash
#############################################################################
# PURPOSE: Build Lambda layers for user-specified Python libraries.
#
# PREREQUISITES:
#   docker
#
# USAGE:
#   Save the python libraries you want in the lambda layer in
#   requirements.txt, then run like this:
#
#   ./build-lambda-layer.sh <path to requirements.txt>
#
# EXAMPLE:
#   To build the Lambda layer zip files:
#       ./build-lambda-layer.sh ./requirements.txt
#
#############################################################################


# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide a valid requirements.txt file."
    echo "USAGE: ./build-lambda-layer.sh <requirements.txt>"
    echo "To build the zip files:"
    echo -e "\t./build-lambda-layer.sh ./requirements.txt"
    exit 1
fi

REQUIREMENTS_FILE="$1"

# Check to see if requirements.txt file exists

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "$REQUIREMENTS_FILE does not exist"
    exit 1
fi

# Check to see if AWS CLI and Docker are installed
docker --version
if [ $? -ne 0 ]; then
  echo "ERROR: install Docker before running this script"
  exit 1
else
  docker ps > /dev/null
  if [ $? -ne 0 ]; then
      echo "ERROR: start Docker before running this script"
      exit 1
  fi
fi

echo "------------------------------------------------------------------------------"
echo "Building Lambda Layer zip file"
echo "------------------------------------------------------------------------------"

# Declare supported Python layer versions
declare -ar supported_python_versions=(3.9 3.10 3.11)
for i in "${supported_python_versions[@]}"
do
  # Delete previously built layer folder and zip file
  rm -rf lambda_layer_python${i} lambda-layer-python${i}.zip
done

docker build --tag=lambda_layer_factory:latest . 2>&1 | tee docker-output.log
if [ $? -eq 0 ]; then
  docker run --rm -v "$PWD":/packages lambda_layer_factory 2>&1 | tee -a docker-output.log
fi
for i in "${supported_python_versions[@]}"
do
  if [[ ! -f "./lambda_layer-python${i}.zip" ]]; then
    echo "ERROR: Failed to build lambda layer zip file."
    exit 1
  fi
done
echo "------------------------------------------------------------------------------"
echo "Verifying the Lambda layer meets AWS size limits"
echo "------------------------------------------------------------------------------"
# See https://docs.aws.amazon.com/lambda/latest/dg/limits.html
ZIPPED_LIMIT=50
UNZIPPED_LIMIT=250
for i in "${supported_python_versions[@]}"
do
  unzip -q -d lambda_layer-python-${i} ./lambda_layer-python${i}.zip
  UNZIPPED_SIZE=$(du -sm ./lambda_layer-python-${i}/ | cut -f 1) 
  ZIPPED_SIZE=$(du -sm ./lambda_layer-python${i}.zip | cut -f 1)
  rm -rf ./lambda_layer-python-${i}/
  if (( $UNZIPPED_SIZE > $UNZIPPED_LIMIT || $ZIPPED_SIZE > $ZIPPED_LIMIT )); then
    echo "ERROR: Deployment package for Python version $i exceeds AWS Lambda layer size limits.";
    exit 1
  fi
done

echo "Lambda layers have been saved to:"
for i in "${supported_python_versions[@]}"
do
  echo "./lambda_layer-python${i}.zip"
done
 
echo "------------------------------------------------------------------------------"
echo "Done"
echo "------------------------------------------------------------------------------"
