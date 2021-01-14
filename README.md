![MIE logo](doc/images/MIE_logo.png)

Media Insights Engine (MIE) is a development framework for building serverless applications that process video, images, audio, and text  on AWS. This repository contains the MIE back-end framework. Users interact with MIE through REST APIs or by invoking MIE Lambda functions directly. You will not find a graphical user interface (GUI) in this repository, but a reference application for MIE that includes a GUI is in the [Media Insights](https://github.com/awslabs/aws-media-insights) repository. 

For a high level summary of MIE and its use cases, please read, [How to Rapidly Prototype Multimedia Applications on AWS with the Media Insights Engine](https://aws.amazon.com/blogs/media/how-to-rapidly-prototype-multimedia-applications-on-aws-with-the-media-insights-engine/) on the AWS Media blog.

# Installation


You can deploy MIE in your AWS account with the following Cloud Formation template:

[![Launch in us-east-1](doc/images/launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mie&templateURL=https://rodeolabz-us-east-1.s3.amazonaws.com/media_insights_engine/v2.0.1/cf/media-insights-stack.template)

The Cloud Formation options for this template are described in the [installation parameters](#installation-parameters) section.

After the stack finished deploying then you should see the following nested stacks (with slightly different names than shown below):

<img src="doc/images/stack_resources.png" width=300>

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

MIE itself does not have a significant cost footprint. The MIE control plane and data plane generally cost less than $1 per month. However, when people talk about the cost of MIE they're generally talking about the cost of running some specific application that was built on top of MIE. Because those costs can vary widely you will need to get pricing information from the documentation for those applications. As a point of reference, read the cost breakdown for the [Content Analysis solution](https://docs.aws.amazon.com/solutions/latest/aws-content-analysis/overview.html#cost).

# Limits

The latest MIE release has been verified to support videos up to 2 hours in duration. 

# Architecture Overview

MIE provides the following three fundamental constructs for building multimedia applications:

1. ***Operators:*** AWS Lambda functions that transform or analyze media objects. MIE includes a Python library that you can use to control how operators execute in workflows and to control how operators persist data.
2. ***Workflows:*** a sequence of operators that work together to derive new media objects or new media metadata. MIE provides a REST API for creating and executing workflows within AWS Step Functions.
3. ***Persistence:*** a storage system for storing or retrieving multimodal data, like binary media objects and plain text metadata. MIE provides a REST API for CRUD functions in a data plane that uses both Amazon S3 and Amazon DynamoDB. 

 The following diagram shows how operators, workflows, and data persistence fit in the MIE architecture:

![](doc/images/MIE-execute-workflow-architecture.png)

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
**System Configuration**
* **MaxConcurrentWorkflows**: Maximum number of workflows to run concurrently. When the maximum is reached, additional workflows are added to a wait queue. Defaults to `10`.
* **DeployAnalyticsPipeline**: If set to true, deploys a Kinesis data stream that can be used by front-end applications to obtain the data generated by workflows. Defaults to `true`.
* **DeployOperatorLibrary**: If set to true, deploys operators for MediaConvert, Rekognition, Transcribe, Translate, et al. Defaults to `true`.
* **DeployTestWorkflow**: If set to true, deploys test workflow which contains operator, stage and workflow stubs for integration testing. Defaults to `false`.
* **EnableXrayTrace**: If set to true, xray tracing is enabled for all supported services in the stack.  Defaults to `false`

# Developers

Join our Gitter chat at [https://gitter.im/awslabs/aws-media-insights-engine](https://gitter.im/awslabs/aws-media-insights-engine). This public chat forum was created to foster communication between MIE developers worldwide.

[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/awslabs/aws-media-insights-engine)

MIE can be extended in the following ways:

* Run existing workflows with custom configurations.
* Create new operators for new types of media analysis or transformation
* Create new workflows using the existing or new operators.
* Stream data to new data storage services, such as Elasticsearch or Amazon Redshift.

For instructions on how to extend MIE, read the API reference and builder's guide in the [Implementation Guide](https://github.com/awslabs/aws-media-insights/blob/master/IMPLEMENTATION_GUIDE.md).

## Security

MIE uses AWS_IAM to authorize REST API requests. The following screenshot shows how to test authentication to the MIE API using Postman. Be sure to specify the AccessKey and SecretKey for your own AWS environment.

<img src="doc/images/sample_postman.png" width=600>

For more information, see the [Implementation Guide](https://github.com/awslabs/aws-media-insights/blob/master/IMPLEMENTATION_GUIDE.md).

# Known Issues

Visit the Issue page in this repository for known issues and feature requests.

# Contributing

See the [CONTRIBUTING](CONTRIBUTING.md) file for how to contribute.

# Logo

The [MIE logo](doc/images/MIE_logo.png) features a clapperboard representing *multimedia*, centered inside a crosshair representing *under scrutiny*. 

# License

See the [LICENSE](LICENSE.txt) file for our project's licensing.

Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
