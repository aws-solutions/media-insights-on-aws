# Developer Quick Start Guide

This document will show you how to build, distribute, and deploy Media Insights Engine (MIE) on AWS and how to implement new operators within the MIE stack.

1. [Prerequisites](#prerequisites)
2. [Building MIE from source code](#building-mie-from-source-code)
3. [Implementing a new MIE Operator](#implementing-a-new-operator-in-mie)

## Prerequisites

Make sure you have the AWS CLI properly configured

Make sure you have Docker installed on your computer

## Building MIE from source code

### Build and distribute the code to AWS

Use the following shell commands to configure the build environment parameters:

    DIST_OUTPUT_BUCKET=[enter the name of your bucket here]
    VERSION=[enter an arbitrary version name here]
    REGION=[enter the name of the region in which you would like to build MIE]

Create an S3 bucket for the MIE build files named `$DIST_OUTPUT_BUCKET-$REGION` using the input you gave above. Example using AWS CLI:

    aws s3 mb s3://$DIST_OUTPUT_BUCKET-$REGION --region $REGION

Run the following build command in your terminal from the `deployment` directory:

    ./build-s3-dist.sh $DIST_OUTPUT_BUCKET $VERSION $REGION


After a few minutes the build files should appear in your S3 bucket.

### Deploy the stack

From your S3 bucket, navigate to `media-insights-solution/<VERSION>/cf/media-insights-stack.template` and copy the object URL.
Use this CloudFormation template to create your stack and deploy MIE.


## Implementing a new Operator in MIE

Operators are Lambda functions that 

* derive new media objects from input media and/or 
* generate metadata by analyzing input media. 

In order to implement a new operator you need to do the following:

1. Write operator Lambda functions
2. Add your operator to the MIE operator library
3. Add your operator to a workflow
4. Add your operator to the Elasticsearch consumer
5. Update the build script to deploy your operator to AWS Lambda
 
Background: 
 
* Operators run as part of an MIE workflow. Workflows are [AWS Step Functions](https://aws.amazon.com/step-functions/) that define the order in which operators run. 

* Operators can be _synchronous_ or _asynchronous_.  Synchronous operators start an  analysis (or transformation) job and get its result in a single Lambda function. Async operators use seperate Lambda functions to start jobs and get their results. Typically, async operators run for several minutes.

* Operator inputs can include a list of media, metadata and the user-defined workflow and/or operator configurations.

* Operator outputs include the execution status, and S3 locators for the newly derived media and metadata objects saved in S3. These outputs get passed to other operators in downstream workflow stages.

* Operators should interact with the MIE data persistence layer via the `MediaInsightsEngineLambdaHelper`, which is located under [lib/MediaInsightsEngineLambdaHelper/](./lib/MediaInsightsEngineLambdaHelper/MediaInsightsEngineLambdaHelper/__init__.py).  

### Step 1: Write operator Lambda functions
***(Difficulty: >1 hour)***

*TL;DR - Copy `source/operators/rekognition/generic_data_lookup.py` to a new directory and change it to do what you want.*

Operators live under `source/operators`.  Create a new folder there for your new operator. 

The MIE Helper library should be used inside an operator to interact with the control plane and data plane. This library lives under `lib/MediaInsightsEngineLambdaHelper/`.

#### Using the MIE Helper library:

Instantiate the helper like this:

```
from MediaInsightsEngineLambdaHelper import OutputHelper
output_object = OutputHelper("my_operator_name")
```

##### How to get Asset and Workflow IDs:

Get the Workflow and Asset ID from the Lambda entrypoint's event object:

```
# Lambda function entrypoint:
def lambda_handler(event, context):
    workflow_id = str(event["WorkflowExecutionId"])
    asset_id = event['AssetId']
```

##### How to get input Media Objects:

Media objects are passed using their location in S3.  Use the `boto3` S3 client access them from S3 using the locations specified in the Lambda entrypoint's event object:

```
def lambda_handler(event, context):
    if "Video" in event["Input"]["Media"]:
        s3bucket = event["Input"]["Media"]["Video"]["S3Bucket"]
        s3key = event["Input"]["Media"]["Video"]["S3Key"]
    elif "Image" in event["Input"]["Media"]:
        s3bucket = event["Input"]["Media"]["Image"]["S3Bucket"]
        s3key = event["Input"]["Media"]["Image"]["S3Key"]
```

##### How to get operator configuration input:

Operator configurations can be accessed from the Lambda entrypoint's event object:

```
collection_id = event["Configuration"]["CollectionId"]
```

##### How to get metadata output from other operators:

Metadata is always passed as input to the next stage in a workflow. Metadata that was output by upstream operators can be accessed from the Lambda entrypoint's event object:

```
job_id = event["MetaData"]["FaceSearchJobId"]
```

##### How to store media metadata to the data plane:

Use `store_asset_metadata()` to store results. For paged results, call that function for each page.

```
from MediaInsightsEngineLambdaHelper import DataPlane
dataplane = DataPlane()
metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
```

##### Store media objects to the data plane S3 bucket

Operators can derive new media objects. For example, the Transcribe operator derives a new text object from an input audio object. Save new media objects with `add_media_object()`, like this:

```
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
operator_object = MediaInsightsOperationHelper(event)
operator_object.add_media_object(my_media_type, bucket, key)
```

The my_media_type variable should be "Video", "Audio", or "Text".

##### Retrieve media objects from the data plane

```
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
operator_object = MediaInsightsOperationHelper(event)
bucket = operator_object.input["Media"][my_media_type]["S3Bucket"]
key = operator_object.input["Media"][my_media_type]["S3Key"]
s3_response = s3.get_object(Bucket=bucket, Key=key)
```

The my_media_type variable should be "Video", "Audio", or "Text".

### Step 2: Add your operator to the MIE operator library 
***(Difficulty: 30 minutes)***

*TL;DR - Edit `source/operators/operator-library.yaml` and add new entries for your operator under the `# Lambda Functions`, `# IAM Roles`, `# Register as operators in the control plane`, `# Export operator names as outputs` sections.*

This step invovles editing the CloudFormation script for deploying the MIE operator library, located at [`source/operators/operator-library.yaml`](source/operators/operator-library.yaml).

#### Create the IAM Role resource

Create a CloudFormation IAM resource that will be used to give your Lambda function the appropriate permissions. MIE operators need `AWSLambdaBasicExecutionRole` plus policies for any other AWS resource and services accessed by the Lambda function. 

#### Create Lambda Function resource

Create a CloudFormation `Lambda::Function` resource for your Operator Lambda function.  If your Operator is _Async_, make sure to also register your monitoring Lambda function.

#### Create the MIE Operator resource using your Lambda function(s)

The MIE Operator custom resource has the following attributes:

```
Type: Custom:CustomResource
Properties:
  ServiceToken: !Ref WorkflowCustomResourceArn
  ResourceType:
    ResourceType
  Name: 
    Name
  Type:
    Type
  Configuration: 
    Configuration
  StartLambdaArn:
    StartLambdaArn
  MonitorLambdaArn:
    MonitorLambdaArn
  StateMachineExecutionRoleArn: !GetAtt StepFunctionRole.Arn
```

***ResourceType***

* Specify the type of resource: `"Operator"`, `"Workflow"`, or `"Stage"`

***Name***

* Specify the name of your Operator

***Type***

* Specify whether your operator is `Sync` or `Async`

***Configuration***
 
* Specify the `MediaType` and `Enabled` fields and add any other configurations needed

***StartLambdaArn***

* Specify the ARN of the Lambda function to start your Operator

***MonitorLambdaArn***

* If your operator is _Async_, specify the ARN of the monitoring Lambda function

#### Export your Operator name as an output

Export your operator as an output like this:
```
  MyOperation:
    Description: "Operation name of MyOperation"
    Value: !GetAtt MyOperation.Name
    Export:
      Name: !Join [":", [!Ref "AWS::StackName", MyOperation]]
```

### Step 3: Add your operator to a workflow 
***(Difficulty: 10 minutes)***

*TL;DR - Edit `source/workflows/MieCompleteWorkflow.yaml` and add your operator under `Resources --> defaultVideoStage --> Operations`*

It's easiest to create a new workflow by copying end editing `MieCompleteWorkflow.yaml`. If you're creating a new workflow, you'll need to know that operators in the same stage will run at the same time (i.e. "in parallel") and stages run sequentially.

### Step 4: Add your operator to the Elasticsearch consumer
***(Difficulty: 30 minutes)***

Edit `source/consumers/elastic/lambda_handler.py`. Add your operator name to the list of `supported_operators`. Define a method to flatten your JSON metadata into Elasticsearch records. Call that method from the `lambda_handler()` entrypoint. 

### Step 5: Update the build script to deploy your operator to AWS Lambda
***(Difficulty: 5 minutes)***

Update the `# Make lambda package` section in [`build-s3-dist.sh`](deployment/build-s3-dist.sh) to zip your operator's Lambda function(s) into the `deployment/dist` directory, like this:

```
zip -r9 my_operator.zip my_operator.py
```

### Step 6: Test your operator

To test your operator you'll want to run a workflow from the command line. Before you can do that you have to get a token from Cognito, like this:

#### Here's how to get a token:

First define the following environment variables. `MIE_USERNAME` and `MIE_PASSWORD` should have been emailed to the email address you specified when you deployed the stack. `MIE_DEVELOPMENT_HOME` should be the path to your `aws-media-insights-engine/` development environment, such as `/Users/myuser/development/aws-media-insights-engine/`.

```
export MIE_STACK_NAME=
export REGION=
export MIE_USERNAME=
export MIE_PASSWORD=
export MIE_DEVELOPMENT_HOME=
```

Now run the following two commands:

```
export MIE_POOL_ID=$(aws cloudformation list-stack-resources --stack-name $MIE_STACK_NAME --region $REGION  --query 'StackResourceSummaries[?LogicalResourceId==`MieUserPool`].PhysicalResourceId' --output text)
export MIE_CLIENT_ID=$(aws cloudformation list-stack-resources --stack-name $MIE_STACK_NAME --region $REGION --query 'StackResourceSummaries[?LogicalResourceId==`MieAdminClient`].PhysicalResourceId' --output text)
export DATAPLANE_BUCKET=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`DataplaneBucket`].OutputValue' --output text)
export WORKFLOW_API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $MIE_STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`WorkflowApiEndpoint`].OutputValue' --output text)  
```

Get the token like this:
```
export MIE_ACCESS_TOKEN=$(VENV=$(mktemp -d); python3 -m venv $VENV; source $VENV/bin/activate; pip --disable-pip-version-check install -q boto3; python3 $MIE_DEVELOPMENT_HOME/tests/getAccessToken.py | tail -n 1; deactivate; rm -rf $VENV)
```

Now you can `curl` MIE APIs with the `-H "Authorization: $MIE_ACCESS_TOKEN"` option.  

#### Test your operator:

Here's how to start the MieCompleteWorkflow with only `MyOperator` enabled:

```
curl -k -X POST -H "Authorization: $MIE_ACCESS_TOKEN" -H "Content-Type: application/json" --data '{"Name":"MieCompleteWorkflow","Configuration":{"defaultVideoStage":{"faceDetection":{"Enabled":false},"celebrityRecognition":{"Enabled":false},"MyOperator":{"Enabled":true},"labelDetection":{"Enabled":false},"personTracking":{"Enabled":false},"Mediaconvert":{"Enabled":false},"contentModeration":{"Enabled":false},"faceSearch":{"Enabled":false}}},"Input":{"Media":{"Video":{"S3Bucket":"'$DATAPLANE_BUCKET'","S3Key":"my_input.mp4"}}}}'  $WORKFLOW_API_ENDPOINT/workflow/execution 
```

#### Monitor your test:

Monitor your test workflow with the following logs:

1. Your operator lambda. To find this log, search the Lambda functions for your operator name.
2. The dataplane API lambda. To find this log, search Lambda functions for "MediaInsightsDataplaneApiStack".
3. The Elasticsearch consumer lambda. To find this log, search Lambda functions for "ElasticsearchConsumer".
