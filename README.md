![scheduled-workflow](https://github.com/awslabs/aws-media-insights-engine/workflows/scheduled-workflow/badge.svg) ![release-workflow](https://github.com/awslabs/aws-media-insights-engine/workflows/release-workflow/badge.svg)

![MIE logo](docs/assets/images/MIE_logo.png)

Media Insights Engine (MIE) is a development framework for building serverless applications that process video, images, audio, and text  on AWS. This repository contains the MIE back-end framework. Users interact with MIE through REST APIs or by invoking MIE Lambda functions directly. You will not find a graphical user interface (GUI) in this repository, but a reference application for MIE that includes a GUI is in the [Media Insights](https://github.com/awslabs/aws-media-insights) repository. 

For a high level summary of MIE and its use cases, please read, [How to Rapidly Prototype Multimedia Applications on AWS with the Media Insights Engine](https://aws.amazon.com/blogs/media/how-to-rapidly-prototype-multimedia-applications-on-aws-with-the-media-insights-engine/) on the AWS Media blog.

# Install

You can deploy MIE in your AWS account with the following Cloud Formation templates. The Cloud Formation stack name must be 12 or fewer characters long.

Region| Launch
------|-----
US East (N. Virginia) | [![Launch in us-east-1](docs/assets/images/launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mie&templateURL=https://rodeolabz-us-east-1.s3.amazonaws.com/media_insights_engine/v2.0.4/media-insights-stack.template)
US West (Oregon) | [![Launch in us-west-2](docs/assets/images/launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=mie&templateURL=https://rodeolabz-us-west-2.s3.us-west-2.amazonaws.com/media_insights_engine/v2.0.4/media-insights-stack.template)

The Cloud Formation options for these one-click deploys are described in the [installation parameters](#installation-parameters) section.

## Build from scratch:

Run the following commands to build and deploy MIE from scratch. Be sure to define values for `MIE_STACK_NAME` and `REGION` first.

```
REGION=[specify a region]
MIE_STACK_NAME=[specify a stack name]
git clone https://github.com/awslabs/aws-media-insights-engine
cd aws-media-insights-engine
cd deployment
VERSION=1.0.0
DATETIME=$(date '+%s')
DIST_OUTPUT_BUCKET=media-insights-engine-$DATETIME
aws s3 mb s3://$DIST_OUTPUT_BUCKET-$REGION --region $REGION
./build-s3-dist.sh $DIST_OUTPUT_BUCKET-$REGION $VERSION $REGION
TEMPLATE={copy "Template to deploy" link from output of build script}
aws cloudformation create-stack --stack-name $MIE_STACK_NAME --template-url $TEMPLATE --region $REGION --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --disable-rollback
```

## Outputs

If you're building applications on MIE then you will need to understand the following resources in the **Outputs** tab of the Cloud Formation stack:

* **DataplaneApiEndpoint** is the endpoint for accessing dataplane APIs to create, update, delete and retrieve media assets
* **DataplaneBucket** is the S3 bucket used to store derived media (_derived assets_) and raw analysis metadata created by MIE workflows.
* **WorkflowApiEndpoint** is the endpoint for accessing the Workflow APIs to create, update, delete and execute MIE workflows.
* **WorkflowCustomResourceArn** is the custom resource that can be used to create MIE workflows in CloudFormation scripts

# Cost

You are responsible for the cost of the AWS services used while running this solution. As of February 2021 the cost for running this solution with the default settings in the us-east-1 (N. Virginia) region is approximately $24 per month without free tiers, or $13 per month with free tiers for 100 workflow executions. This is based on workflows processing live action videos 10 minutes in duration. 

### Approximate monthly cost, excluding all free tiers:

| AWS Service | Quantity | Cost |
| --- | --- | --- |
| AWS Lambda | 100 workflows | $4.75 / mo |
| API Gateway | 1 million workflows | $3.50 / mo |
| Kinesis Data Stream | 100 workflows | $12.56 / mo |
| SQS | 1 million workflows | $0.40 / mo |
| SNS | n/a | No charge |
| Xray | 100 workflows | $.0005 / mo |
| S3 | 100 workflows | $2.3 / mo |
| Dynamo DB | 1 million workflows | $.025 / mo |

Each additional 100 workflow executions will cost roughly $2, or higher for videos longer than 10 minutes and lower for videos shorter than 10 minutes.

It is expected that most MIE use-cases will be completely covered by the free tier for all services except Amazon Kinesis and AWS Lambda. The costs for the Amazon Kinesis data stream ($12.56/mo) and the Workflow Scheduler lambda ($3.73/mo) will remain relatively unchanged, regardless of how many workflows execute.

# Limits

The Cloud Formation stack name for MIE must be 12 or fewer characters long. This will ensure all the resources in MIE stack remain under the maximum length allowed by Cloud Formation.

MIE does not inherently limit media attributes such as file size or video duration. Those limitations depend on the services used in user-defined workflows. For example, if a workflow uses Amazon Rekognition, then that workflow will be subject to the limitations listed in the [guidelines and quotas for Amazon Rekognition](https://docs.aws.amazon.com/rekognition/latest/dg/limits.html).

# Architecture Overview

Deploying this solution with the default parameters builds the following environment in the AWS Cloud.

![](docs/assets/images/MIE-architecture-diagram.png)

The AWS CloudFormation template provisions the following resources:

1.	An Amazon API Gateway resource for the control plane REST API.
2.	AWS Lambda and Amazon Simple Queue Service (Amazon SQS) resources to support workflow orchestration and translating user-defined workflows into AWS Step Functions.
3.	The following Amazon DynamoDB tables to persist workflow related data:
  a.	Workflow – This table records user-defined workflows.
  b.	Workflow Execution – This table records the details of every workflow execution.
  c.	Operations – This table records details for each operator in the operator library, such references to Lambda functions and default run-time parameters.
  d.	Stage – This table records the auto-generated step function code needed for each operator.
  e.	System – This table records system wide configurations, such as max concurrent workflows.
4.	AWS Step Functions when a user defines a new workflow using the workflow API.
5.	AWS Lambda functions for the MIE operator library. This includes the following operators:
      *	Celebrity Recognition - An asynchronous operator to identify celebrities in a video using Amazon Rekognition. 
      * Content Moderation - An asynchronous operator to identify unsafe content in videos using Amazon Rekognition.
      * Face Detection - An asynchronous operator to identify faces in videos using Amazon Rekognition.
      * Face Search - An asynchronous operator to identify faces from a custom face collection in videos using Amazon Rekognition.
      * Label Detection - An asynchronous operator to identify objects in a video using Amazon Rekognition.
      * Person Tracking - An asynchronous operator to identify people in a video using Amazon Rekognition.
      * Shot Detection - An asynchronous operator to identify camera shots in a video using Amazon Rekognition.
      * Text Detection – An asynchronous operator to identify text in a video using Amazon Rekognition.
      * Technical Cue Detection – An asynchronous operator to identify technical cues such as end credits, color bars, and black bars in a video using Amazon Rekognition.
      * Comprehend Key Phrases – An asynchronous operator to find key phrases in text using Amazon Comprehend.
      * Comprehend Entities – An asynchronous operator to find references to real-world objects, dates, and quantities in text using Amazon Comprehend.
      * Create SRT Captions – A synchronous operator to generate SRT formatted caption files from a video transcript generated by Amazon Transcribe
      * Create VTT Captions - A synchronous operator to generate VTT formatted caption files from a video transcript generated by Amazon Transcribe
      * Media Convert - An asynchronous operator to transcode input video into mpeg4 format using AWS Elemental MediaConvert.
      * Media Info – A synchronous operator to read technical tag data for video files.
      * Polly - An asynchronous operator that turns input text into speech using Amazon Polly.
      * Thumbnail - An asynchronous operator that generates thumbnail images for an input video file using AWS Elemental MediaConvert.
      * Transcribe - An asynchronous operator to convert input audio to text using Amazon Transcribe.
      * Translate - An asynchronous operator to translate input text using Amazon Translate.

6.	An Amazon API Gateway resource for the data plane REST API.
7.	Amazon Simple Storage Service (Amazon S3), DynamoDB, and DynamoDB Streams for media and metadata data storage.
8.	Amazon Kinesis Data Streams resources to provide an interface for external applications to access data in the MIE data plane.

MIE includes an operator library with several commonly used media analysis functions. However, workflows are entirely use-case dependent and therefore must be user-defined. This procedure is explained in the [Implementation Guide](IMPLEMENTATION_GUIDE.md#44-implementing-a-new-operator-in-mie).


### Architecture components:

* ***Workflow API:*** Use this API to create, update, delete, execute, and monitor workflows.

* ***Control plane:*** includes the API and state machines for workflows.  Workflow state machines are generated from MIE operators.  As operators within the state machine are executed, they interact with the MIE data plane to store and retrieve derived asset and metadata generated from the workflow.  

* ***Operators:*** these are generated state machines that perform media analysis or transformation operation.

* ***Workflows:*** these are generated state machines that execute a number of operators in sequence.

* ***Data plane:*** this stores the media assets and metadata generated by workflows. 

* ***Data plane API:*** this is used to create, update, delete and retrieve  media assets and metadata.

* ***Data plane pipeline:*** this stores metadata for an asset that can be retrieved using an object's AssetId and Metadata type.  Writing data to the pipeline triggers a copy of the data to be stored in a **Kinesis Stream**, which is developers can hook up their front-end applications.

# Installation Parameters

You can deploy MIE and the demo GUI in your AWS account with the [one-click deploy buttons](#installation) shown above. 

## Required parameters

**Stack Name**: Name of stack.

## Optional parameters

**System Configuration**
* **MaxConcurrentWorkflows**: Maximum number of workflows to run concurrently. When the maximum is reached, additional workflows are added to a wait queue. Defaults to `10`.
* **DeployAnalyticsPipeline**: If set to true, deploys a Kinesis data stream that can be used by front-end applications to obtain the data generated by workflows. Defaults to `true`.
* **DeployOperatorLibrary**: If set to true, deploys operators for MediaConvert, Rekognition, Transcribe, Translate, et al. Defaults to `true`.
* **DeployTestWorkflow**: If set to true, deploys test workflow which contains operator, stage and workflow stubs for integration testing. Defaults to `false`.
* **EnableXrayTrace**: If set to true, xray tracing is enabled for all supported services in the stack.  Defaults to `false`
* **SendAnonymousData**: If set to true, send anonymous data about MIE performance to AWS to help improve the quality of this solution. For more information, see the below. Defaults to `false`

# Developers

Join our Gitter chat at [https://gitter.im/awslabs/aws-media-insights-engine](https://gitter.im/awslabs/aws-media-insights-engine). This public chat forum was created to foster communication between MIE developers worldwide.

[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/awslabs/aws-media-insights-engine)

MIE can be extended in the following ways:

* Run existing workflows with custom configurations.
* Create new operators for new types of media analysis or transformation
* Create new workflows using the existing or new operators.
* Stream data to new data storage services, such as Elasticsearch or Amazon Redshift.

For instructions on how to extend MIE, read the API reference and builder's guide in the [Implementation Guide](IMPLEMENTATION_GUIDE.md).

## Security

MIE uses AWS_IAM to authorize REST API requests. The following screenshot shows how to test authentication to the MIE API using Postman. Be sure to specify the AccessKey and SecretKey for your own AWS environment.

<img src="docs/assets/images/sample_postman.png" width=600>

For more information, see the [Implementation Guide](IMPLEMENTATION_GUIDE.md#step-6-test-your-new-workflow-and-operator).

## Privacy

When deploying MIE cloud formation templates, anonymous data, such as that shown below, will be sent to AWS. This information is used to help improve the quality of the MIE solution. To opt-out from this reporting, set the `SendAnonymousData` parameter to `false` in the Cloud Formation stack details.


```
{
    "Solution": "SO0163",
    "UUID": "d84a0bd5-7483-494e-8ab1-fdfaa7e97687",
    "TimeStamp": "2021-03-01T20:03:05.798545",
    "Data": {
        "Version": "2.0.4",
        "CFTemplate": "Created"
    }
}
```

# Uninstall

To uninstall MIE, delete the CloudFormation stack. This will delete all the resources created by the MIE template except the Dataplane S3 bucket and the DataplaneLogs bucket. These two buckets are retained when the solution stack is deleted in order to help prevent accidental data loss. You can use either the AWS Management Console or the AWS Command Line Interface (AWS CLI) to empty, then delete those S3 buckets after deleting the CloudFormation stack.

# Known Issues

Visit the Issue page in this repository for known issues and feature requests.

# Contributing

See the [CONTRIBUTING](CONTRIBUTING.md) file for how to contribute.

# Logo

The [MIE logo](docs/assets/images/MIE_logo.png) features a clapperboard representing *multimedia*, centered inside a crosshair representing *under scrutiny*. 

# License

See the [LICENSE](LICENSE.txt) file for our project's licensing.

Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
