# AWS Lambda Layer factory

This factory creates AWS Lambda layers for user-specified Python libraries. Separate zip files will be generated for Python 3.9, 3.10, 3.11 execution environments.

## USAGE:

### 1. Preliminary Setup:

1. Install [Docker](https://docs.docker.com/) on your workstation.


### 2. Build Lambda layers

```
cd deployment/lambda_layer_factory
```

Put your desired Python libraries in a requirements.txt file, following standard pip conventions. For example:

```
echo "boto3==1.9.134" >> requirements.txt
```

Run the `build-lambda-layer.sh` script to build a Lamba layer containing the python packages you specified above.

```
./build-lambda-layer.sh ./requirements.txt
```

### 3. Validate

To validate that the Lambda layer includes certain libraries, for example `pymediainfo`, do this:

```
cd .../media-insights-on-aws/
PYTHONPATH=./source/lib/MediaInsightsEngineLambdaHelper/ python3 -c "import pymediainfo"
```

If you do not see a ModuleNotFoundError then the layer contains library is missing from the layer.
