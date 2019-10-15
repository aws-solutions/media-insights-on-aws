#!/bin/bash
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
MIE_STACK_NAME=scribe-demo01
DIST_OUTPUT_BUCKET=media-insights-engine
REGION=us-east-1
PROFILE=mie

#################### NO CHANGES NEEDED BELOW THIS LINE ########################
# Make the output bucket unique by adding time string suffix:
VERSION=1.0.1
DATETIME=$(date '+%s')
DIST_OUTPUT_BUCKET=$DIST_OUTPUT_BUCKET-$DATETIME
echo "Deploying stack name: "$MIE_STACK_NAME
echo "Using output bucket: "$DIST_OUTPUT_BUCKET"-"$REGION
sleep 2

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

aws cloudformation create-stack --stack-name $MIE_STACK_NAME --template-url  https://s3.amazonaws.com/$DIST_OUTPUT_BUCKET-$REGION/media-analysis-solution/$VERSION/cf/media-analysis-workflow-stack.template --region $REGION --parameters \
ParameterKey=DeployOperatorLibrary,ParameterValue=true \
ParameterKey=DeployRekognitionWorkflow,ParameterValue=false \
ParameterKey=DeployInstantTranslateWorkflow,ParameterValue=false \
ParameterKey=DeployTestWorkflow,ParameterValue=false \
ParameterKey=DeployTranscribeWorkflow,ParameterValue=true \
ParameterKey=DeployAnalyticsPipeline,ParameterValue=false \
ParameterKey=TranscriberApp,ParameterValue=false \
--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --profile $PROFILE --disable-rollback

# Tell bash to stop echoing
set +x

# Wait for create-stack to complete
status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus')
while [ "$status" == "CREATE_IN_PROGRESS" ]; do sleep 5; status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION  --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus'); done
echo "Create stack $MIE_STACK_NAME status: $status"
if [ "$status" != "CREATE_COMPLETE" ]; then exit 1; fi

# This log group must be removed manually or TranscriberApp will fail to deploy:
echo "Removing log group: /aws/lambda/prod-aws-captions-customresource"
aws logs delete-log-group --log-group-name /aws/lambda/prod-aws-captions-customresource --region us-east-1 --profile mie

# Tell bash to echo commands, so we can debug the create-stack command:
set -x
# Deploy workflow and dataplane resources
echo "------------------------------------------------------------------------------"
echo "Updating the stack to include TranscriberApp"
echo "------------------------------------------------------------------------------"

aws cloudformation update-stack --stack-name $MIE_STACK_NAME --template-url  https://s3.amazonaws.com/$DIST_OUTPUT_BUCKET-$REGION/media-analysis-solution/$VERSION/cf/media-analysis-workflow-stack.template --region $REGION --parameters \
ParameterKey=DeployOperatorLibrary,ParameterValue=true \
ParameterKey=DeployRekognitionWorkflow,ParameterValue=false \
ParameterKey=DeployInstantTranslateWorkflow,ParameterValue=false \
ParameterKey=DeployTestWorkflow,ParameterValue=false \
ParameterKey=DeployTranscribeWorkflow,ParameterValue=true \
ParameterKey=DeployAnalyticsPipeline,ParameterValue=false \
ParameterKey=TranscriberApp,ParameterValue=true \
--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --profile $PROFILE

# Tell bash to stop echoing
set +x

# Wait for create-stack to complete
status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus')
while [ "$status" == "UPDATE_IN_PROGRESS" ]; do sleep 5; status=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION  --output json --profile $PROFILE | jq -r '.Stacks | .[] | .StackStatus'); done
echo "Create stack $MIE_STACK_NAME status: $status"
if [ "$status" != "UPDATE_COMPLETE" ]; then exit 1; fi

echo "Done"
