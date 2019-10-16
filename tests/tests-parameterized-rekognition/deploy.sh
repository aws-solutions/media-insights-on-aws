#!/bin/bash

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script is for testing purposes only. Use it to deploy
# the MIE stack with every deploy option enabled.
#
# USAGE:
#   Set the following env vars:
#     MIE_STACK_NAME
#     DIST_OUTPUT_BUCKET
#     REGION
#     PROFILE
#   Then run `./deploy.sh`
#
###############################################################################
MIE_STACK_NAME=mie03
# REGION=us-west-2
DIST_OUTPUT_BUCKET=media-insights-engine
PROFILE=default

#################### NO CHANGES NEEDED BELOW THIS LINE ########################
# Make the output bucket unique by adding time string suffix:
VERSION=1.0.1
DATETIME=$(date '+%s')
DIST_OUTPUT_BUCKET=$DIST_OUTPUT_BUCKET-$DATETIME
# shortcut for REGION naming
if [ $MIE_STACK_NAME == "mie01" ]; then REGION="us-east-1"; fi
if [ $MIE_STACK_NAME == "mie02" ]; then REGION="us-east-2"; fi
if [ $MIE_STACK_NAME == "mie03" ]; then REGION="us-west-2"; fi
echo "Deploying stack name: "$MIE_STACK_NAME
echo "Using output bucket: "$DIST_OUTPUT_BUCKET"-"$REGION
sleep 2


# Docker is required to build lambda layers, so fail if Docker is not running:
docker --version
if [ $? -ne 0 ]; then
    echo "ERROR: install and start Docker before running this script"
    exit 1
fi

cd ../deployment

# Exit if MIE_STACK_NAME stack if it already exists
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --profile $PROFILE 2> /dev/null > /dev/null
if [ $? -eq 0 ]; then
  echo "ERROR: $MIE_STACK_NAME stack already exists."
  exit 1
fi


aws s3 rb s3://$DIST_OUTPUT_BUCKET-$REGION --force --profile $PROFILE 2> /dev/null
aws s3 mb s3://$DIST_OUTPUT_BUCKET-$REGION --region $REGION --profile $PROFILE

# Build lambda layer and cloud formation templates
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $VERSION $REGION $PROFILE
if [ $? -ne 0 ]; then
  echo "ERROR: Build script failed."
  exit 1;
fi

# Tell bash to echo commands, so we can debug the create-stack command:
set -x
# Deploy workflow and dataplane resources
echo "------------------------------------------------------------------------------"
echo "Creating the stack"
echo "------------------------------------------------------------------------------"

# Deploy workflow and dataplane resources
aws cloudformation create-stack --stack-name $MIE_STACK_NAME --template-url  https://s3.amazonaws.com/$DIST_OUTPUT_BUCKET-$REGION/media-insights-solution/$VERSION/cf/media-insights-stack.template --region $REGION --parameters \
ParameterKey=DeployOperatorLibrary,ParameterValue=true \
ParameterKey=DeployRekognitionWorkflow,ParameterValue=true \
ParameterKey=DeployInstantTranslateWorkflow,ParameterValue=false \
ParameterKey=DeployTestWorkflow,ParameterValue=false \
ParameterKey=MaxConcurrentWorkflows,ParameterValue=10 \
ParameterKey=DeployComprehendWorkflow,ParameterValue=false \
ParameterKey=DeployKitchenSinkWorkflow,ParameterValue=true \
ParameterKey=DeployAnalyticsPipeline,ParameterValue=true \
ParameterKey=DeployDemoSite,ParameterValue=false \
ParameterKey=ApiIpList,ParameterValue="72.21.198.64/32" \
--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --profile $PROFILE --disable-rollback

# Tell bash to stop echoing
set +x

# Wait for create-stack to complete
status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus')
while [ "$status" == "CREATE_IN_PROGRESS" ]; do sleep 5; status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION  --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus'); done
echo "Create stack $MIE_STACK_NAME status: $status"
if [ "$status" != "CREATE_COMPLETE" ]; then exit 1; fi

echo "Done"
