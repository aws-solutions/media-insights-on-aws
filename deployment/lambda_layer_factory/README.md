# AWS Lambda Layer factory

This factory creates AWS Lambda layers for user-specified Python libraries. Separate zip files will be generated for Python 3.7, 3.8, and 3.9 execution environments.

## USAGE:

### 1. Preliminary Setup: 
1. Install [Docker](https://docs.docker.com/) and the [AWS CLI](https://aws.amazon.com/cli/) on your workstation.
2. Setup credentials for AWS CLI (see http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).
3. Create IAM Role with Lambda and S3 access:
```
# Create a role with S3 access
ROLE_NAME=lambda_layer_factory
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document '{"Version":"2012-10-17","Statement":{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}}'
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess --role-name $ROLE_NAME
```

### 2. Build and Publish Lambda layers
```
cd deployment/lambda_layer_factory
```

Put your desired Python libraries in a requirements.txt file, following standard pip conventions. For example:
```
echo "boto3==1.9.134" >> requirements.txt
```

Run the `build-lambda-layer.sh` script to build and deploy a Lamba layer containing the python packages you specified above.
```
./build-lambda-layer.sh requirements.txt s3://my_bucket/lambda_layers/ us-west-2
```

### 3. Validate

To validate that the Lambda layers were created, do this:
```
aws lambda list-layer-versions --layer-name lambda_layer-python37 --output text --query 'LayerVersions[0].LayerVersionArn'
aws lambda list-layer-versions --layer-name lambda_layer-python38 --output text --query 'LayerVersions[0].LayerVersionArn'
aws lambda list-layer-versions --layer-name lambda_layer-python39 --output text --query 'LayerVersions[0].LayerVersionArn'
```

To validate that the Lambda layer includes certain libraries, for example `pymediainfo`, do this:
```
cd .../media-insights-on-aws/
PYTHONPATH=./source/lib/MediaInsightsEngineLambdaHelper/ python3 -c "import pymediainfo"
```
If you do not see a ModuleNotFoundError then the layer contains library is missing from the layer.
