#!/bin/bash

echo "================================================================================"
echo "Installing packages from requirements.txt"
echo "================================================================================"
pip3.7 install -r /packages/requirements.txt -t /packages/lambda_layer-python-3.7/python/lib/python3.7/site-packages
pip3.6 install -r /packages/requirements.txt -t /packages/lambda_layer-python-3.6/python/lib/python3.6/site-packages

echo "================================================================================"
echo "Creating zip files for Lambda layers"
echo "================================================================================"
cd /packages/lambda_layer-python-3.7/
zip -q -r9 /packages/lambda_layer-python3.7.zip .
cd /packages/lambda_layer-python-3.6/
zip -q -r9 /packages/lambda_layer-python3.6.zip .

# Clean up build environment
cd /packages/
rm -rf /packages/lambda_layer-python-3.7/
rm -rf /packages/lambda_layer-python-3.6/

#cp /packages/lambda_layer-python3.6.zip /packages/lambda_layer-python3.7.zip /data

echo "Zip files have been saved to docker volume /data. You can copy them locally like this:"
echo "docker run --rm -it -v \$(pwd):/packages <docker_image>"
echo "================================================================================"
echo "Done."
