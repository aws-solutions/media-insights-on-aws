#!/bin/bash
#############################################################################
# PURPOSE: Build and optionally deploy a Lambda layer for user-specified Python libraries.
#
# PREREQUISITES:
#   docker, aws cli
#
# USAGE:
#   Save the python libraries you want in the lambda layer in
#   requirements.txt, then run like this:
#
#   ./build-lambda-layer.sh <path to requirements.txt> [s3 bucket path] [aws region]
#
# EXAMPLE:
#   To build but not publish the Lambda layer zip files:
#       ./build-lambda-layer.sh ./requirements.txt
#   To build the zip files and publish Lambda layers:
#       ./build-lambda-layer.sh ./requirements.txt s3://my_bucket/lambda_layers/ us-west-2
#
#############################################################################


# Check to see if input has been provided:
if [ -z "$1" ] || ([ ! -z "$2" ] && [ -z "$3" ]); then
    echo "Please provide a fully qualified s3 bucket for the lambda layer code to reside and the region of the deploy."
    echo "USAGE: ./build-lambda-layer.sh <requirements.txt> [s3 bucket path] [aws region]"
    echo "To build but not publish the Lambda layer zip files:"
    echo -e "\t./build-lambda-layer.sh ./requirements.txt"
    echo "To build the zip files and publish Lambda layers:"
    echo -e "\t./build-lambda-layer.sh ./requirements.txt s3://my_bucket/lambda_layers/ us-west-2"
    exit 1
fi

REQUIREMENTS_FILE=$1
S3_BUCKET=$(echo $2 | cut -f 3 -d "/")
S3_FQDN=$2
REGION=$3

# Check to see if requirements.txt file exists

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "$REQUIREMENTS_FILE does not exist"
    exit 1
fi

# Check to see if AWS CLI and Docker are installed
docker --version
if [ $? -ne 0 ]; then
    echo "ERROR: install and start Docker before running this script"
    exit 1
fi

echo "------------------------------------------------------------------------------"
echo "Building Lambda Layer zip file"
echo "------------------------------------------------------------------------------"
docker build --tag=lambda_layer_factory:latest .
docker run --rm -it -v $(pwd):/packages lambda_layer_factory
if [[ ! -f ./lambda_layer-python3.6.zip ]] || [[ ! -f ./lambda_layer-python3.7.zip ]]; then
    echo "ERROR: Failed to build lambda layer zip file."
    exit 1
fi
echo "------------------------------------------------------------------------------"
echo "Verifying the Lambda layer meets AWS size limits"
echo "------------------------------------------------------------------------------"
# See https://docs.aws.amazon.com/lambda/latest/dg/limits.html
unzip -q -d lambda_layer-python-3.6 ./lambda_layer-python3.6.zip
unzip -q -d lambda_layer-python-3.7 ./lambda_layer-python3.7.zip
ZIPPED_LIMIT=50
UNZIPPED_LIMIT=250
UNZIPPED_SIZE_36=`du -sm ./lambda_layer-python-3.6/ | cut -f 1`
ZIPPED_SIZE_36=`du -sm ./lambda_layer-python3.6.zip | cut -f 1`
UNZIPPED_SIZE_37=`du -sm ./lambda_layer-python-3.7/ | cut -f 1`
ZIPPED_SIZE_37=`du -sm ./lambda_layer-python3.7.zip | cut -f 1`
if (( $UNZIPPED_SIZE_36 > $UNZIPPED_LIMIT || $ZIPPED_SIZE_36 > $ZIPPED_LIMIT || $UNZIPPED_SIZE_37 > $UNZIPPED_LIMIT || $ZIPPED_SIZE_37 > $ZIPPED_LIMIT)); then
	echo "ERROR: Deployment package exceeds AWS Lambda layer size limits.";
	rm -f ./lambda_layer-python3.6.zip
	rm -f ./lambda_layer-python3.7.zip
	rm -rf ./lambda_layer-python-3.6/
	rm -rf ./lambda_layer-python-3.7/
	exit 1
fi
echo "Lambda layers have been saved to ./lambda_layer-python3.6.zip and ./lambda_layer-python3.7.zip."

if [ ! -z $S3_FQDN ]; then
    which aws > /dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: install the AWS CLI before running this script"
        exit 1
    fi
    ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
    echo "------------------------------------------------------------------------------"
    echo "Validating access to S3"
    echo "------------------------------------------------------------------------------"
    aws s3 mb $S3_BUCKET 2> /dev/null
    aws s3 ls $S3_BUCKET > /dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed accessing $S3_FQDN"
    fi
    echo "------------------------------------------------------------------------------"
    echo "Publishing Lambda Layer to AWS account $ACCOUNT_ID"
    echo "------------------------------------------------------------------------------"
    LAMBDA_LAYERS_BUCKET=lambda-layers-$ACCOUNT_ID
    LAYER_NAME_36=lambda_layer-python36
    LAYER_NAME_37=lambda_layer-python37
    # create temp working dir for zip files
    aws s3 mb s3://$LAMBDA_LAYERS_BUCKET > /dev/null
    # Warn user if layer already exists
    aws lambda list-layer-versions --layer-name $LAYER_NAME_36 | grep -q "\"LayerVersions\": \[" 
    if [ $? -eq 0 ]; then
        echo "WARNING: AWS Layer with name $LAYER_NAME_36 already exists."
        read -r -p "Are you sure you want to overwrite $LAYER_NAME_36? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]
        then
            aws s3 cp lambda_layer-python3.6.zip s3://$LAMBDA_LAYERS_BUCKET
            aws lambda publish-layer-version --layer-name $LAYER_NAME_36 --content S3Bucket=$LAMBDA_LAYERS_BUCKET,S3Key=lambda_layer-python3.6.zip --compatible-runtimes python3.6
            aws s3 rm s3://$LAMBDA_LAYERS_BUCKET/lambda_layer-python3.6.zip
            arn36=$(aws lambda list-layer-versions --layer-name lambda_layer-python36 --output text --query 'LayerVersions[0].LayerVersionArn')            
        fi
    fi
    aws lambda list-layer-versions --layer-name $LAYER_NAME_37 | grep "\"LayerVersions\": \["
    if [ $? -eq 0 ]; then
        echo "WARNING: AWS Layer with name $LAYER_NAME_37 already exists."
        read -r -p "Are you sure you want to overwrite $LAYER_NAME_37? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]
        then
            aws s3 cp lambda_layer-python3.7.zip s3://$LAMBDA_LAYERS_BUCKET
            aws lambda publish-layer-version --layer-name $LAYER_NAME_37 --content S3Bucket=$LAMBDA_LAYERS_BUCKET,S3Key=lambda_layer-python3.7.zip --compatible-runtimes python3.7
            aws s3 rm s3://$LAMBDA_LAYERS_BUCKET/lambda_layer-python3.7.zip
            arn37=$(aws lambda list-layer-versions --layer-name lambda_layer-python37 --output text --query 'LayerVersions[0].LayerVersionArn')
        fi
    fi
    # remove temp working dir for zip files
    aws s3 rb s3://$LAMBDA_LAYERS_BUCKET/ > /dev/null    
    echo "Lambda layers have been published. Use the following ARNs to attach them to Lambda functions:"
    echo $arn36
    echo $arn37
fi

echo "------------------------------------------------------------------------------"
echo "Done"
echo "------------------------------------------------------------------------------"