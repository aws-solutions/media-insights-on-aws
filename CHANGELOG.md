# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.4] - 2021-11-8

### CI/CD Automation:

* Clean up chalice generated CloudFormation templates (#623, #624, #625)

### Security:

* Scope down IAM policy used for by DynamoDB Streams Lambda function for logging to Cloudwatch (#628)

## [3.0.3] - 2021-10-05

### New:

* Statically define the MediaConvert endpoint to avoid throttling (#606) 

### CI/CD Automation:

* Add an option to specify an AWS profile to the build script so build assets can be uploaded to a user-specified AWS account (#601)
* Require users to acknowledge Amazon S3 security advice during the build script prior to uploading build assets to Amazon S3 (#603)

### Fixed:

* Fix a pagination bug that prevented the control plane from handling more than 50 concurrent workflow executions (#609)

### Documentation:

* Fix an error in the documentation for building MIE from scratch (#602)

### Security:

* Update Python modules known to have possible security implications (#611)


## [3.0.2] - 2021-08-18

### New:

* Add new e2e tests to validate CRUD functions in the workflow API for parallel data  and terminologies in Amazon Translate. (#543)

### CI/CD Automation:

* Allow parent stacks to specify both the solution version for the botoconfig string. This, combined with the existing functionality to specify the solution id, means that applications which use MIE can correctly describe themselves to the internal AWS mechanisms that count solution deployments. (#574)

### Fixed:

* When processing long videos, workflows may fail if the video transcript exceeds the max length allowed by Amazon Polly. This behavior was changed so that worklfows will skip the Polly operation and output a warning if the text is too long (#543)

* The API version reported by the /version resource under the data plane and control plane APIs was incorrectly defined as version 2.0.0. It is now correctly defined as version 3.0.0. (#576)

## [3.0.1] - 2021-07-22

### Documentation:

* Sphinx generated API documentation copied to the Implementation Guide (#532)

### Security:

* Validate SSL certificates when making calls to API Gateway (#525)
* Update Python modules known to have possible security implications (#526)
* Grant read permission to the dataplane bucket for Translate and Transcribe operators so they can access custom vocabularies, custom terminologies, etc. (#531)

### CI/CD Automation:

* Add a one-click deploy option for the AWS region in eu-west-1 Ireland (#536)

## [3.0.0] - 2021-06-25

### New:

* Workflows can now use media files from any S3 bucket as inputs. Prior to this release workflows required input media files to reside within the MIE data plane bucket. In order to use this capability the ARN for the external S3 bucket must be specified in the ExternalBucketArn parameter in the MIE base template for Cloud Formation (#489)

* Added a new parameter in the MIE Cloud Formation template that allows users and parent stacks to opt-out from anonymous data collection (#509)

* Added a new parameter in the MIE Cloud Formation template that allows parent stacks to associate their AWS solution id with MIE's boto3 calls. This helps the AWS Solution Builder team improve the quality of published solutions.  

### Changes:

* Media files are no longer copied to the data plane S3 bucket when recording new assets. This change will break backwards compatibility for applications that assume the S3Bucket property for assets is always the data plane bucket. This change is also the only change that caused MIE's major release number to bump from v2.5.0 to v3.0.0. (#489)

* If input media files cannot be found at the S3 location specified within workflow execution requests then return an error to the HTTP client indicating that the file could not be found. (#507)

### Security:

* Upgrade urllib version (#490, 491)

### CI/CD Automation:

* Validate S3 bucket ownership before uploading build artifacts (#499)

### Documentation:

* The implementation guide now explains about how to start workflows programmatically and provides Python code samples for doing so. These examples can be used to set up an S3 trigger for workflow execution. (#489)

## [2.0.5] - 2021-04-09

### New:

* Compatibility with build pipeline for the official AWS Media Insights Engine solution (#436, #442) 
* Add user-agent string for (#424)

### Changes:

* Relocate opt-out option for anonymous data collection so it resembles the pattern used by other AWS solutions (#388)
* Use solution builder's convention for s3 bucket names (#436)

### Security:

* Allow user-specified KMS keys for Comprehend (#407, #409)

### CI/CD Automation:

* Resolve cfn nag failures and warnings (#393, #440)
* Resolve viperlight failures and warnings (#418)

### Documentation:

* Fix broken hyperlink to Implementation Guide (#385)
* Document uninstall instructions (#412)
* Apply feedback from tech writing (#416)


## [2.0.4] - 2021-03-05

### New:

* Add Parallel Data as an input to the TranslateWebCaptions operator (#386)
* Add a Cloud Formation option to send anonymous data about MIE performance to AWS to help improve the quality of the MIE solution. (#388)

### Security:

* Enhance strategies for achieving least privilege (#383)
* (#393) Enhance strategies for achieving least privilege

### Documentation:

* Fix broken links in the Implementation Guide (#385)


## [2.0.3] - 2021-02-11

### Changes:

* Update AWS Lambda functions to use the latest python runtime, Python 3.8. (#362)
    
### Fixed:

* Fixed workflow IAM policies to support managing custom vocabularioes and terminologies with Transcribe and Translate. (#359)
* Added the default MaxConcurrentWorkflow configuration to the table used for storing system configuration. (#360)
* Improved the robustness of asset reprocessing. (#369)

### CI/CD Automation:

* Added status badges for automated tests to README.

### Documentation:

* Added Implementation Guide for MIE, including new info about the kinesis data stream and limitations with the /workflow/operation API resource. (#353)


## [2.0.2] - 2021-01-22

Added many new features to help developer usability and resolved several bugs. Notable changes include; simpler command line usage of the build script with named parameters, MIE / API versions returned via a new API route and as a Cloudformation Output, and tagging of all MIE resources.

Also added a new GitHub Pages site that contains API reference documentation (https://awslabs.github.io/aws-media-insights-engine/)

### Changes:

* All MIE resources are now tagged (#292)
* Several build script updates (#293)
* New Transcribe operators that can be used for either video or audio files (#280)
* New auto-documenting API functionality that parses API method docstrings (#295)
* Added new API routes /version to both MIE APIs that return MIE version and API version (#301)
* Added a new API route /service to the workflow api for AWS Service configuration (#312)
* Missing docstrings in APIs added (#326)

### Fixed:

* Fixed issue where build script would fail if docker was not running (#64)
* Fixed issue in GET /asset/metadata test (#285)
* Fixed issue where resource names being too long caused stack create failure (#304)

### Security:

* Implemented a security mechanism that allows the StepFunction role to be scoped down to MIE specific lambdas (#291)

### Documentation:

* New documentation website that is hosted on Github Pages (#295)

### Misc:

* Build no longer compiles mediainfo from source and instead uses the published version (#265)


## [2.0.1] - 2020-12-23

Version 2.0.1 of the Media Insights Engine introduces one major feature alongside the addition of automated build, test, and release pipelines. Minor bug fixes / security enhancements were included as well.

The new feature provides the ability to support human in the loop subtitle generation and editing workflows. This work required several new operators and substantial changes to the workflow API.

The new release pipelines enable the MIE development team to easily accept Pull Requests from community contributors and allows us to release new versions of MIE at a more rapid pace.

### Changes:

* Reduced the default configuration for concurrent workflows from 10 to 5 (#299)
* New wait state lambdas for editing and human in the loop workflows (#299)
* Several new operators for subtitle generation (#299)
* New API routes in the workflow API for transcribe service config (#299)
* New workflow statuses for resume and waiting (#299)
* Several modifications to the workflow API handler for supporting editing workflows (#299)
* DynamoDB stream configured for the workflow execution table (#299)
* Refactored technical cues and shot detection operators to use service provided configuration (#307)

### CI/CD Automation:

* Modified the build script to write template url to a file (#323)
* Created a second build script that does not attempt to build lambda layer or helper library (#323)
* Added exit codes to testing scripts (#323)
* New "PR" test workflow (#323)
* New "Scheduled" build, test, deploy, workflow (#323)
* New "Release" workflow (#323)
* Added code coverage analysis to unit tests (#323)

### Security:

* Enabled access logging and encryption on dataplane S3 bucket (#282)

### Fixed:

* Fix bug in retrieve asset metadata method in the MIE helper lib (#299)

### Misc:

Version bumped MIE helper lib


## [2.0.0] - 2020-12-04

Version 2.0.0 of the Media Insights Engine introduces some significant changes and important new features. Most notably the ability to deploy the framework multiple times within the same region and the ability to trace requests with AWS X-Ray. This release also introduces an overhaul to the testing strategy of the framework and provides updated documentation on it. Several minor changes and bug fixes were also included.

### Changes:

* Moved source/tests to test  (#266)
* Renamed test stack to accurately reflect the contained resources (#266)
* Removed operator library deployment parameter (setting to false prohibited the stack from being deployed) (#266)
* All stack resources updated to use a unique name (#259)
* Updated the workflow API to not create actual stepfunctions resources for stage objects (#256)
* Handle errors that terminate MIE state machines (#272)

### New:

* Add X-Ray tracing to MIE stack (#252)

### CI/CD Automation:

* Multiple deployments of the framework supported in one region (#260)
* Tiered test strategy in place (unit, integ, e2e) (#253)
* IAM authentication support for tests #266 (#266)

### Fixed:

* Removed the IAM tag condition for step functions execution; this was causing a rollback failure (#190)
* Version locked the s3 signature version to s3v4 in the dataplane API (#255)
* Version locked the python runtime for both MIE API's (#257)
* Version locked dependencies for the MIE lambda layer build script (#263)
* Added a function to only patch modules for xray if on AWS compute (#266)

### Documentation:

* Updated documentation on how to test the framework (#266)

### CI/CD Automation:

Removed stale pipeline configs


## [1.0.0] - 2020-10-07

This release (v1.0.0) focuses on removing cruft and reorganizing the core MIE framework to make it easier for developers to build applications on MIE.

### New:

* Simplified MIE code base:
  * Back-end / Front-end split
  * Major version rev indicates incompatiblity with previous front-ends

* New security features:
  * Support for AWS_IAM

* New installation options
  * Option 1: Install front-end only
  * Option 2: Install front-end / back-end bundle

### Documentation:

* IMPLEMENTATION_GUIDE.md moved to front-end repo.


## [0.1.8] - 2020-06-22

* This release includes new support for Rekogntion Video Segment Detection. More info on Video Segment Detection can be found here: https://aws.amazon.com/blogs/media/streamline-media-analysis-tasks-with-amazon-rekognition-video/

### New:

* You will have two new Video operations to choose from in the workflow configuration dialog. You can detect both technical cues and shots.

### Documentation:

* General reformatting of the readme page.
* Additional steps on the installation of MIE are now available.
* Users are encouraged to join the MIE public chat forum on Gitter. This forum was created to foster communication between MIE users external to AWS.


## [0.1.7] - 2020-04-09

This release includes a new feature for reprocessing videos and an important bug fix for the MediaInfo operator. 

### New:

* The analysis view in the GUI includes a new link to “Perform Additional Analysis”, as shown in the screenshot below. This link takes you to the upload page where you can run a different workflow configuration without uploading the video again. The resulting analysis data will be saved using the same asset id.

### Documentation:

* Users are encouraged to join the MIE public chat forum on Gitter. This forum was created to foster communication between MIE users external to AWS.

### Bug Fixes

* MediaInfo released a new version (20.03) last week which broke the existing MediaInfo operator in MIE. As a temporary workaround this MIE release is configured to use the previous version of MediaInfo (v19.09).


## [0.1.6] - 2020-03-25

This release includes new operators, cost optimizations, improved documentation for developers, security enhancements, and lots of bug fixes. 

### New:

* Text in Video: words are searchable and shown under the ML Vision tab in the GUI
* MediaInfo: codec info and other file metadata is searchable and shown in the GUI under the video player
* Transcode: MIE leverages MediaConvert to support many more video and image formats including Flash, Quicktime, MXF, and MKV. See https://docs.aws.amazon.com/mediaconvert/latest/ug/reference-codecs-containers.html for a full list of supported video formats.

### Cost:

* Reduced cost by deploying the free tier for Elasticsearch
* Pricing information for MIE resources is now included in README.md (https://github.com/awslabs/aws-media-insights-engine/blob/master/README.md)

### Documentation:

* The Developer guide is now included in IMPLEMENTATION_GUIDE.md (https://github.com/awslabs/aws-media-insights-engine/blob/master/IMPLEMENTATION_GUIDE.md)

### Security:

* Subresource integrity (SRI) checks ensure the validity of GUI assets
* GUI prevents users form uploading unsupported file types (such as .exe and .zip)
* If users upload invalid media files then those files will be removed by the Mediainfo operator.

### Fixed:

* Bounding boxes no longer appear outside the video player
* Videos without sound or dialog no longer produce a workflow error


## [0.1.6] - 2019-12-13

This Media Insights Engine Beta 0.1.5 release includes changes necessary to support 2 hour long videos.

### New:

* The key to supporting 2 hour videos was to allow step functions to pass a pagination token from one "check status" Lambda invocation to another. Now, Rekognition operators will persist 10 pages at a time, then stop and pass the pagination token to the step function so it can repeatedly restart the "check status" Lambda until there are no more pages left to read.
* Prior to this release, Rekognition operators would timeout when trying to save large quantities of paged results, which was often the case with label_detection and face_detection.
* Increase timeouts and memory allocations for Lambda functions based on test results from a 2 hour movie.
* Add API documentation to README
* Split input text in the translate operator so it does not exceed the 5000 characters max allowed by AWS Translate service limit.
* Split bulk elasticsearch inserts in order to avoid exceeding max payload size
* If data is empty, skip ES insert. Data is often empty for operators like content moderation when processing non-explicit videos.

### GUI changes:

* Remove unusued GUI artifacts for Polly and AutoML.
* Fix autofill for 1Password on the Login form
* Raise max file upload size to 2GB in the GUI.
* Allow analysis button to open in new tab
* Fade delete alert after 5 seconds
* Change workflow configuration form so users only have to set the language for Transcribe and Translate once. Used to be that users would have to set that language preference twice, but now, since both Transcribe and Translate use the same source language, users can just specify this option once.

### CloudFormation template changes:

* Make the Cloudfront URL a clickable link in the outputs from both the webapp CF template and the base stack template.
* Update the email template for the Cognito invite message so it includes a link to the stack.
