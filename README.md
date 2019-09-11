# Media Insights Engine

Welcome to the preview of the Media Insights Engine project!

# Overview

The Media Insights Engine (MIE) is a framework that enables you to quickly build applications that extract key details about the content of your media files using AWS machine learning (ML) and computational services.  The project includes a serverless architecture on AWS as well as a sample web application for exploring your data.

The serverless architecture provides the following building blocks:


**Controlplane:** Workflow orchestration, scheduling, and lifecycle management of MIE components.

**Dataplane:** Storage, retrieval, and search functionality for assets and metadata derived by workflows.

**Operators:** Transform or extract metadata from media.  

**Stages:** Group of operators that can be executed in parallel for increased workflow performance.

**Workflows:** Execution of a sequence of operators or stages in a pipeline.



# Installation / Deployment
Deploy the demo architecture and application in your AWS account and start exploring your media.

Region| Launch
------|-----
US East (Virgina) | [![Launch in us-east-1](doc/images/launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mie&templateURL=https://rodeolabz-us-east-1.s3.amazonaws.com/media-insights-solution/v0.1.0/cf/media-insights-stack.template)
# Usage

###  Sample application

![](doc/images/MIEDemo.gif)

The Media Insights sample application runs an MIE workflow that contains many of the ML content analysis services available on AWS and stores them in a search engine for easy exploration.  A web based GUI is used to search and visualize the resulting data along-side the input media.  Analysis and transformations included in this application include:

* **AWS MediaConvert** to separate a video package into video and audio tracks for downstream analysis.
* **AWS Rekognition** computer vision to identify objects, celebrities, people, faces and moderated content. 
* **AWS Transcribe** to convert speech in audio to text.
* **AWS Translate** to translate text to new languages.
* **AWS Comprehend** to identify key phrases and entitites that occur in the audio of the video.

Data are stored in AWS Elasticsearch search engine and can be retrieved using Lucene queries in the Collection view search page.


### Example use cases for Media Insights Engine
 
MIE is a reusable architecture that can support many different applications.  Examples:
 
* **Content analysis analysis and search** - Detect objects, people, celebrities and sensitive content, transcribe audio and detect entities, relationships and sentiment.  Explore and analyze media using full featured search and advanced data visualization.  This use case is implemented in the included sample application.
* **Automatic Transcribe and Translate** - Generate captions for Video On Demand content using speech recognition.  
* **Content Moderation** - Detect and edit moderated content from videos.

# Developer Quickstart

The Media Analysis Engine is built to be extended for new use cases.  You can:

* Run existing workflows using custom runtime confgurations.
* Create new operators for new types of analysis or transformations of your media.
* Create new workflows using the existing operators and/or your own operators.
* Add new data consumers to provide data management that suits the needs of your application.

See the [Developer Guide](https://github.com/awslabs/aws-media-insights-engine/blob/master/DEVELOPER_QUICK_START) for more information on extending the application for a custom use case.

API Reference - Coming soon!
Builder's guide - Coming soon!

# Known Issues

Visit the Issue page in this repository for known issues and feature requests.

# Release History

# Contributing

See the [CONTRIBUTING](https://github.com/awslabs/aws-media-insights-engine/blob/master/CONTRIBUTING) file for how to contribute.

# License

See the [LICENSE](https://github.com/awslabs/aws-media-insights-engine/blob/master/LICENSE) file for our project's licensing.

Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
