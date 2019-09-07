#!/bin/bash

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script is for testing purposes only. Use it to deploy
# the MIE stack with every deploy option enabled.
#
# USAGE:
#   Set the following env vars:
#     STACK_NAME
#     DIST_OUTPUT_BUCKET
#     REGION
#   Then run `./deploy.sh`
#
###############################################################################
MIE_STACK_NAME=mie03
REGION=us-east-2
DIST_OUTPUT_BUCKET=media-insights-engine
PROFILE=default

#################### NO CHANGES NEEDED BELOW THIS LINE ########################
# Make the output bucket unique by adding time string suffix:
VERSION=1.0.1
DATETIME=$(date '+%s')
DIST_OUTPUT_BUCKET=$DIST_OUTPUT_BUCKET-$DATETIME
echo "Deploying stack name: "$MIE_STACK_NAME
echo "Using output bucket: "$DIST_OUTPUT_BUCKET"-"$REGION
sleep 2


#Tests are currently failing unless we build the lambda layer. Docker is used to build those layers, so fail if docker is not running:
docker --version
if [ $? -ne 0 ]; then
    echo "ERROR: install and start Docker before running this script"
    exit 1
fi

cd /Users/ianwow/development/MediaInsightsEngine/deployment

for STACK_NAME in $ES_STACK_NAME $MIE_STACK_NAME
  do
  aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --profile $PROFILE 2> /dev/null > /dev/null
  if [ $? -eq 0 ]; then
      # workaround dataplane bucket not removing in delete-stack
      DATAPLANE_BUCKET=$(aws cloudformation list-stack-resources --stack-name $STACK_NAME --output json --profile $PROFILE 2> /dev/null | jq -r '.StackResourceSummaries | .[] | select(.LogicalResourceId=="DataplaneBucket") | .PhysicalResourceId')
      if [ ! -z "$DATAPLANE_BUCKET" ]; then
        echo "Deleting old dataplane bucket: "$DATAPLANE_BUCKET
        aws s3 rb s3://$DATAPLANE_BUCKET --force --profile $PROFILE
      fi
      echo "Deleting old stack: "$STACK_NAME
      aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION --profile $PROFILE
      status=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --output json --profile $PROFILE 2> /dev/null | jq -r '.Stacks | .[] | .StackStatus')
      while [ "$status" == "DELETE_IN_PROGRESS" ]; do sleep 5; echo -n "."; status=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --output json --profile $PROFILE 2> /dev/null | jq -r '.Stacks | .[] | .StackStatus'); done
      echo "Stack $STACK_NAME has been deleted"
  fi
done

aws s3 rb s3://$DIST_OUTPUT_BUCKET-$REGION --force --profile $PROFILE 2> /dev/null
aws s3 mb s3://$DIST_OUTPUT_BUCKET-$REGION --region $REGION --profile $PROFILE
# this takes 3 minutes:
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $VERSION $REGION $PROFILE
if [ $? -ne 0 ]; then
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
ParameterKey=DeployInstantTranslateWorkflow,ParameterValue=true \
ParameterKey=DeployTestWorkflow,ParameterValue=true \
ParameterKey=DeployTranscribeWorkflow,ParameterValue=true \
ParameterKey=MaxConcurrentWorkflows,ParameterValue=10 \
ParameterKey=DeployComprehendWorkflow,ParameterValue=true \
ParameterKey=DeployKitchenSinkWorkflow,ParameterValue=true \
ParameterKey=DeployAnalyticsPipeline,ParameterValue=true \
ParameterKey=DeployDemoSite,ParameterValue=true \
ParameterKey=TranscriberApp,ParameterValue=false \
ParameterKey=ApiIpList,ParameterValue="0.0.0.0/0" \
--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --profile $PROFILE --disable-rollback

# Tell bash to stop echoing
set +x

# Wait for create-stack to complete
status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus')
while [ "$status" == "CREATE_IN_PROGRESS" ]; do sleep 5; status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION  --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus'); done
echo "Create stack $MIE_STACK_NAME status: $status"
if [ "$status" != "CREATE_COMPLETE" ]; then exit 1; fi

DATAPLANE_BUCKET=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --query 'Stacks[].Outputs[?OutputKey==`DataplaneBucket`].OutputValue' --output text --profile $PROFILE)
DATAPLANE_API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --query 'Stacks[].Outputs[?OutputKey==`DataplaneApiEndpoint`].OutputValue' --output text --profile $PROFILE)
WORKFLOW_API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --query 'Stacks[].Outputs[?OutputKey==`WorkflowApiEndpoint`].OutputValue' --output text --profile $PROFILE)
ELASTICSEARCH_DOMAINNAME=`aws es list-domain-names --query 'DomainNames[].DomainName' --output text --region $REGION --profile $PROFILE`
ELASTICSEARCH_ENDPOINT=`aws es describe-elasticsearch-domain --domain-name $ELASTICSEARCH_DOMAINNAME --query 'DomainStatus.Endpoint' --output text --region $REGION --profile $PROFILE`

echo "VUE_APP_ELASTICSEARCH_ENDPOINT="https://$ELASTICSEARCH_ENDPOINT >> ../webapp/.env
echo "VUE_APP_WORKFLOW_API_ENDPOINT="$WORKFLOW_API_ENDPOINT >> ../webapp/.env
echo "VUE_APP_DATAPLANE_API_ENDPOINT="$DATAPLANE_API_ENDPOINT >> ../webapp/.env
echo "VUE_APP_DATAPLANE_BUCKET="$DATAPLANE_BUCKET >> ../webapp/.env
echo Endpoint URL: $WORKFLOW_API_ENDPOINT

# Create face collection if it doesn't exist
aws rekognition list-faces --collection-id family_faces --region $REGION --profile $PROFILE
if [ $? -ne 0 ]; then
wget https://upload.wikimedia.org/wikipedia/commons/9/9e/20180602_FIFA_Friendly_Match_Austria_vs._Germany_Rainer_Pariasek_850_0540.jpg
aws s3 cp 20180602_FIFA_Friendly_Match_Austria_vs._Germany_Rainer_Pariasek_850_0540.jpg s3://$DATAPLANE_BUCKET/ --profile $PROFILE
aws rekognition create-collection --collection-id family_faces --region $REGION --profile $PROFILE
aws rekognition index-faces --image '{"S3Object":{"Bucket":"'$DATAPLANE_BUCKET'","Name":"20180602_FIFA_Friendly_Match_Austria_vs._Germany_Rainer_Pariasek_850_0540.jpg"}}' --collection-id "family_faces" --region $REGION --profile $PROFILE
rm 20180602_FIFA_Friendly_Match_Austria_vs._Germany_Rainer_Pariasek_850_0540.jpg
fi
aws rekognition list-faces --collection-id family_faces --region $REGION --profile $PROFILE
if [ $? -ne 0 ]; then
echo "ERROR: Failed to create face collection"
exit 1;
fi

BUCKET_NAME="burkleaa-files"
IMAGE_FILENAME="test-media/sample-image.jpg"
VIDEO_FILENAME="test-media/sample-video.mp4"

# Test image processing
curl -k -X POST -H "Content-Type: application/json" --data '{"Name":"ParallelRekognitionWorkflowImage","Configuration": {"parallelRekognitionStageImage":{"faceSearchImage":{"MediaType": "Image","Enabled": true, "CollectionId": "family_faces"},"labelDetectionImage":{"MediaType": "Image","Enabled": true},"celebrityRecognitionImage":{"MediaType": "Image","Enabled": true},"contentModerationImage":{"MediaType": "Image","Enabled": true},"faceDetectionImage":{"MediaType": "Image","Enabled": true}}},"Input": {"Media": {"Image":{"S3Bucket":"'$BUCKET_NAME'","S3Key":"'$IMAGE_FILENAME'"}}}}' $WORKFLOW_API_ENDPOINT/workflow/execution | jq -r '.Workflow | .Stages | .parallelRekognitionStageImage | .AssetId'

# Test video processing
curl -k -X POST -H "Content-Type: application/json" --data '{"Name":"MieCompleteWorkflow","Configuration": {"defaultVideoStage":{"faceSearch":{"CollectionId":"family_faces","MediaType": "Video","Enabled": true}}},"Input": {"Media": {"Video":{"S3Bucket":"'$BUCKET_NAME'","S3Key":"'$VIDEO_FILENAME'"}}}}'  $WORKFLOW_API_ENDPOINT/workflow/execution | jq -r '.Workflow | .Stages | .parallelRekognitionStage | .AssetId'

# Wait for video processing to finish
STEP_FUNCTION_ARN=$(aws stepfunctions list-state-machines --query 'stateMachines[?name==`ParallelRekognitionWorkflow`].stateMachineArn' --output text --region $REGION --profile $PROFILE)
status=$(aws stepfunctions list-executions --state-machine-arn $STEP_FUNCTION_ARN --query 'executions[0].status' --output text --region $REGION --profile $PROFILE)
while [ "$status" == "RUNNING" ]; do sleep 5; status=$(aws stepfunctions list-executions --state-machine-arn $STEP_FUNCTION_ARN --query 'executions[0].status' --output text --region $REGION --profile $PROFILE); done
echo "ParallelRekognitionWorkflow status: $status"


echo "Done"
