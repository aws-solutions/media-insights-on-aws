
## TODO

* [x] Fix dynamo bugs on restart processing
* [ ] Empty all buckets and add depends on buckets to custom resource
* [x] Create Custom Vocabulary - in custom resource
* [x] Bug when video autorewinds but does not reset caption index to zero
* [ ] Validate video max length 2 hours
* [ ] Multiple vocabularies / locales
* [x] Pick locale / vocabulary
* [ ] Expert mode see all captions and edit?
* [ ] Validate caption times on save
* [x] Word confidence
* [ ] Blog
* [x] Private GitHub repository
* [x] Preserve name and description during re-runs
* [x] Rename videos and edit description
* [x] Search videos based on description
* [x] Hide view video links for Processing tab
* [x] Mark as complete
* [x] Namespace table and buckets using service name
* [x] Delete videos
* [x] Reprocess videos
* [x] Tab badges for videos
* [x] Select last tab
* [x] Default tab to last selected for videos
* [x] Add caption blocks past the end of video bug
* [x] Play to end of video play bug
* [x] Document Elastic Transcoder service linked role
* [x] Delete previous transcribe jobs
* [x] List of errored jobs
* [x] Handle transcribe service limits (retry)
* [x] Refresh on videos page
* [x] Login system
* [x] Auth system for Lambda (API keys)
* [x] API Gateway end points
* [x] Video caption editor
* [x] Download of captions
* [x] Lambda for Transcode
* [x] Lambda for Transcribe
* [x] Lambda for Captions
* [x] Lambda for Comprehend
* [x] Lambda IAM role per function
* [x] Dynamo Schema
* [x] Cloudformation - serverless
* [x] Update diagram
* [x] Upload video function
* [x] S3 CORS
* [x] Auto save captions every 20 seconds


# Data below this is just rough notes

## Custom vocabularies

	https://docs.aws.amazon.com/transcribe/latest/dg/how-it-works.html#how-vocabulary

## Building the front end

	https://www.sitepoint.com/single-page-app-without-framework/
	
	https://github.com/Graidenix/vanilla-router
	
	https://getbootstrap.com/docs/4.0/getting-started/introduction/
	
	http://handlebarsjs.com/
	
	https://medium.com/codingthesmartway-com-blog/getting-started-with-axios-166cb0035237
	
	https://datatables.net/
	
	https://loading.io/

## Convert DynamoDB responses:

	https://gist.github.com/igorzg/c80c0de4ad5c4028cb26cfec415cc600

## Define GSI

	https://gist.github.com/DavidWells/c7df5df9c3e5039ee8c7c888aece2dd5

## Async Lambda node 8.10

	https://aws.amazon.com/blogs/compute/node-js-8-10-runtime-now-available-in-aws-lambda/

## Deploying using Serverless

pip install --upgrade awscli

Install globally:

	npm i -g serverless
	npm i serverless-stack-output
	npm i serverless-finch
	npm i serverless-plugin-scripts
	npm i aws-sdk (Optional)

	https://serverless.com/blog/serverless-express-rest-api/
	
	https://github.com/serverless/examples/blob/master/aws-node-rest-api-with-dynamodb/serverless.yml
	
	https://github.com/serverless/examples/tree/master/aws-node-env-variables
	
List of all lifecycle events in Serverless:

	https://gist.github.com/HyperBrain/bba5c9698e92ac693bb461c99d6cfeec#package

## Limit increase for Transcribe

And handle errors when queue is full

## CORS survival guide

	https://serverless.com/blog/cors-api-gateway-survival-guide/
	
## Lifecycle hooks:
	
	https://gist.github.com/HyperBrain/50d38027a8f57778d5b0f135d80ea406
	
## Bug for S3 bucket events CORS:

	Created

## Update available 5.3.0 → 6.4.1

	Run npm i -g npm to update 

## Elastic transcoder

	https://github.com/ACloudGuru/serverless-framework-video-example/blob/master/backend/transcode-video-firebase-enabled/index.js

## Blog examples

	https://aws.amazon.com/blogs/machine-learning/discovering-and-indexing-podcast-episodes-using-amazon-transcribe-and-amazon-comprehend/

	https://aws.amazon.com/blogs/compute/implementing-serverless-video-subtitles/

	https://aws.amazon.com/blogs/machine-learning/get-started-with-automated-metadata-extraction-using-the-aws-media-analysis-solution/

## Dropzone upload directly to S3

	https://stackoverflow.com/questions/34526851/upload-files-to-amazon-s3-with-dropzone-js-issue
	
	starts-with signing
	https://cwhite.me/avoiding-the-burden-of-file-uploads/
	
	https://gist.github.com/chrisseto/8828186#file-put-upload-to-s3-via-dropzone-js
	
	https://tutorialzine.com/2017/07/javascript-async-await-explained

## Styling dropzone

	https://codepen.io/fuxy22/pen/pyYByO

## Step functions

	https://serverless.com/blog/how-to-manage-your-aws-step-functions-with-serverless/



