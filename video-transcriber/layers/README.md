# Lambda Layer for AWS SDK

This project creates and deployes a layer for the AWS Node.js SDK.

## Installation

Download the AWS Node.js SDK:

	cd package/nodejs/
	npm install
	cd ../../

to download the AWS SDK dependency.

Then change back to the root of the layers/ folder and execute:

	serverless deploy --accountId <account id>

to package and deploy the layer to AWS.
