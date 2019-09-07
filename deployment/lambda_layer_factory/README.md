# AWS Lambda Layer factory

This factory creates AWS Lambda layers for user-specified Python libraries. Two seperate zip files will be generated for Python 3.6 and 3.7 execution environments.

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

(Optional) To get the latest version of the MediaInsightsEngineLambdaHelper package, build the "whl" file and include it in the requirements.txt like this:
```
cd deployment/lambda_layer_factory
git clone git+ssh://git.amazon.com/pkg/MediaInsightsEngineLambdaHelper
cd MediaInsightsEngineLambdaHelper/
python3 setup.py bdist_wheel
cp dist/*.whl ../
cd ..
rm -rf MediaInsightsEngineLambdaHelper/
echo "/packages/Media_Insights_Engine_Lambda_Helper-0.0.1-py3-none-any.whl" >> requirements.txt
``` 

Run the `build-lambda-layer.sh` script to build and deploy a Lamba layer containing the python packages you specified above.
```
./build-lambda-layer.sh requirements.txt s3://my_bucket/lambda_layers/ us-west-2
```

### 3. Validate

Validate that the Lambda layers were created
```
aws lambda list-layer-versions --layer-name lambda_layer-python36 --output text --query 'LayerVersions[0].LayerVersionArn'
aws lambda list-layer-versions --layer-name lambda_layer-python37 --output text --query 'LayerVersions[0].LayerVersionArn'
```
