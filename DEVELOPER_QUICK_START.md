# Developer Quick Start Guide

This document will show you how to build, distribute, and deploy Media Insights Engine (MIE) on AWS and how to implement new operators within the MIE stack.

1. [Prerequisites](#prerequisites)
2. [Building MIE from source code](#building-mie-from-source-code)
3. [Implementing a new MIE Operator](#implementing-a-new-operator-in-mie)
   1. [Write your Lambda functions](#write-your-lambdas)
   2. [Automate the deployment of your operator](#automate-the-deployment-of-your-operator)
   3. [Update build-s3-dist.sh](#update-build-s3-distsh)

## Prerequisites

Make sure you have the AWS CLI properly configured

Make sure you have Docker installed on your computer

## Building MIE from source code

### Build and distribute the code to AWS

Use the following shell commands to configure the build environment parameters:

    DIST_OUTPUT_BUCKET=[enter the name of your bucket here]
    VERSION=[enter an arbitrary version name here]
    REGION=[enter the name of the region in which you would like to build MIE]

Create an S3 bucket for the MIE build files named `$DIST_OUTPUT_BUCKET-$REGION` using the input you gave above.

Run the following build command in your terminal from the `deployment` directory:

    ./build-s3-dist.sh $DIST_OUTPUT_BUCKET $VERSION $REGION


After a few minutes the build files should appear in your S3 bucket.

### Deploy the stack

From your S3 bucket, navigate to `media-insights-solution/main/cf/media-insights-workflow-stack.template` and use this CloudFormation template to create your stack and deploy MIE.


## Implementing a new Operator in MIE

MIE generates workflows using [AWS Step Functions service](https://aws.amazon.com/step-functions/) state machines.  Operators are created by implementing resources (e.g. Lambda) that can plug in to MIE state machines as tasks and registering them as operators using the MIE API.  MIE currently only supports Lambda Operator resources.

Operators can be _synchronous_ (Sync) or _asynchronous_ (Async).  Synchronous operators complete before return control to the invoker while asynchronous operators return control to the invoker when the operation is successfully initiated, but not complete.  Asynchronous operators require an additional monitoring task to check the status of the operation.

The `MediaInsightsEngineLambdaHelper` Python package helps to implement Lambda operators by managing inputs and outputs your Lambda functions have the correct JSON interfaces expected by MIE.  The code for the helper is located [here](./lib/MediaInsightsEngineLambdaHelper/MediaInsightsEngineLambdaHelper/__init__.py).  

Operator inputs include a list of Media, Metadata and the operator Configuration plus ids for the workflow execution the operator is part of and the asset the operator is processing.

Operator outputs include the execution status, media and metadata locators that will be passed along to other stages of the workflow.

Operators can interact with the MIE data persistence layer via the data plane API.  The data plane support storage and retrieval of media and metadata produced by operators in the workflow.

### Write your Lambda functions

The Operator library Lambda functions are found under source/operators.  Create a new folder for your new Operator(s) there. 

Use the MIE Helper to interact with the control plane and data plane as follows.

#### Use the MediaInsightsEngineLambdaHelper to load the operator input from the workflow context:

    helper = MediaInsightsOperationHelper(event)

##### Get Asset/Workflow ID
    
    asset_id = helper.asset_id
    workflow_id = helper.workflow_execution_id

##### Get input Media Objects

Input media objects are passed using their location in S3.  Use the `boto3` S3 client access them from S3:

    bucket = helper.input["Media"]["Text"]["S3Bucket"]
    key = helper.input["Media"]["Text"]["S3Key"]
    s3_media = S3Client.get_object(Bucket=bucket, Key=key)

##### Get input workflow metadata

Input workflow metadata are passed as key-value pairs.

    value = key = helper.input["Metadata"]["Key"]

##### Store asset metadata to the data plane

**JSON:**

Use the data plane API's POST `/metadata/{asset_id}` route using the request body below.

**Paginated Inputs:**

For JSON arrays, use the data plane API's POST `/metadata/{asset_id}?paginated=true` route and make a POST request for each element of the array.

On the last element of the array, make a POST request to the data plane api's `/metadata/{asset_id}?paginated=true&end=true` route to indicate the end of the paginated JSON.

**DataPlane POST /metadata/{asset_id} body:**
        
    {
        "OperatorName": "{some_operator}",
        "Results": "{json_formatted_results}",
        "WorkflowId": "{workflow-id}"
    }

Pass your JSON object in the `Results` field of the request body. The `OperatorName` can be an arbitrary string, this is used to name your JSON file and can be used for metadata retrieval.

##### Store media objects to the data plane S3 bucket

1. To add media objects to the data plane, use the data plane API's GET `/mediapath/{asset_id}/{workflow_id}` route to get an S3 bucket and key in the MIE data plane to upload your media to. Add the file name for your media to the S3 key

2. Upload media to the S3 bucket using the `boto3` S3 client

3. Use the data plane API's POST `/metadata/{asset_id}` route to store a dictionary containing the S3 bucket and key of your media object to the data plane

For example:

    "Results": {
            "S3Bucket": "mie-dataplanebucket-1ho3ukz2hs0vz",
            "S3Key": "private/assets/bdc25687-aa10-4df5-ac65-f2ff058680ea/workflows/3de6fe88-0eca-4baf-879f-edfc1d08062f/Captions.srt"
        }

##### Retrieve media objects from the data plane

- Use the data plane API's GET `/metadata/{asset_id}` route to retrieve the dictionary containing the S3 bucket and key of your media object

- Metadata is also passed as input to the next stage in the workflow. So if you are trying to retrieve metadata from a previous stage of the workflow, you can also get it from the helper's input field

      metadata = helper.input["MetaData"]

##### Retrieve asset metadata from the data plane

- Use the data plane API's GET `/metadata/{asset_id}/{operator_name}` route to retrieve the metadata for a specific operator where `operator_name` is the arbitrary string used to store the metadata

- Use the data plane API's GET `/metadata/{asset_id}` route to retrieve all the metadata and media objects for your operator as a sequence of paginated results (see below)

Paginated Results:

A `cursor` is passed back in the response if there are more elements in the response object. Continue passing the cursor back as a query parameter by making a GET request to the data plane API's `/metadata/{asset_id}?cursor={cursor}` route to retrieve subsequent elements of the response metadata.

### Automate the deployment of your Operator 

The CloudFormation script for deploying the MIE operator library to AWS is located in [`source/operators/operator-library.yaml`](source/operators/operator-library.yaml)

MIE operators, stages and workflows can be deployed to AWS using the MIE Workflow API or using the MIE CloudFormation custom resources.  This section will walk through the CloudFormation method.  

##### Create IAM Role resource

Create a CloudFormation IAM resource that will be used to give your Lambda function the appropriate permissions. MIE operators need `AWSLambdaBasicExecutionRole` plus policies for any other AWS resource and services accessed by the Lambda function. 

###### Create Lambda Function resource

Create a CloudFormation `Lambda::Function` resource for your Operator Lambda function.  If your Operator is _Async_, make sure to also register your monitoring Lambda function.

###### Create the MIE Operator resource using your Lambda function(s)

The MIE Operator custom resource has the following attributes:

*Operator*

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

*ResourceType*

> Specify the type of resource: `"Operator"`, `"Workflow"`, or `"Stage"`

*Name*

> Specify the name of your Operator

*Type*

> Specify whether your operator is `Sync` or `Async`

*Configuration*
 
 > Specify the `MediaType` and `Enabled` fields and add any other configurations needed

*StartLambdaArn*

> Specify the ARN of the Lambda function to start your Operator

*MonitorLambdaArn*

> If your operator is _Async_, specify the ARN of the monitoring Lambda function

##### Export your Operator name as output in the CloudFormation `OperatorLibrary` stack

#### Update [`build-s3-dist.sh`](deployment/build-s3-dist.sh)

1. Create the Lambda package
2. Zip the Lambda function(s) into the `deployment/dist` directory