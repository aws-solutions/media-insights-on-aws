#!/bin/bash
###############################################################################
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# PURPOSE:
#   Build cloud formation templates for the Media Insights Engine
#
# USAGE:
#  ./build-s3-dist.sh {SOURCE-BUCKET} {VERSION} {REGION} [PROFILE]
#    SOURCE-BUCKET should be the name for the S3 bucket location where the
#      template will source the Lambda code from.
#    VERSION should be in a format like v1.0.0
#    REGION needs to be in a format like us-east-1
#    PROFILE is optional. It's the profile  that you have setup in ~/.aws/config
#      that you want to use for aws CLI commands.
#
###############################################################################

# Check to see if input has been provided:
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name,  version where the lambda code will eventually reside and the region of the deploy."
    echo "USAGE: ./build-s3-dist.sh SOURCE-BUCKET VERSION REGION [PROFILE]"
    echo "For example: ./build-s3-dist.sh mie01 v1.0.0 us-east-1 default"
    exit 1
fi

bucket=$1
version=$2
region=$3
if [ -n "$4" ]; then profile=$4; fi

# Check if region is supported:
if [ "$region" != "us-east-1" ] &&
   [ "$region" != "us-east-2" ] &&
   [ "$region" != "us-west-1" ] &&
   [ "$region" != "us-west-2" ] &&
   [ "$region" != "eu-west-1" ] &&
   [ "$region" != "eu-west-2" ] &&
   [ "$region" != "eu-central-1" ] &&
   [ "$region" != "ap-south-1" ] &&
   [ "$region" != "ap-northeast-1" ] &&
   [ "$region" != "ap-southeast-1" ] &&
   [ "$region" != "ap-southeast-2" ] &&
   [ "$region" != "ap-northeast-1" ] &&
   [ "$region" != "ap-northeast-2" ]; then
   echo "ERROR. Rekognition operatorions are not supported in region $region"
   exit 1
fi

# Make sure wget is installed
if ! [ -x "$(command -v wget)" ]; then
  echo "ERROR: Command not found: wget"
  echo "ERROR: wget is required for downloading lambda layers."
  echo "ERROR: Please install wget and rerun this script."
  exit 1
fi

# Build source S3 Bucket
if [[ ! -x "$(command -v aws)" ]]; then
echo "ERROR: This script requires the AWS CLI to be installed. Please install it then run again."
exit 1
fi

# Get reference for all important folders
template_dir="$PWD"
dist_dir="$template_dir/dist"
source_dir="$template_dir/../source"
workflows_dir="$template_dir/../source/workflows"
webapp_dir="$template_dir/../source/webapp"
echo "template_dir: ${template_dir}"

# Create and activate a temporary Python environment for this script.
echo "------------------------------------------------------------------------------"
echo "Creating a temporary Python virtualenv for this script"
echo "------------------------------------------------------------------------------"
python -c "import os; print (os.getenv('VIRTUAL_ENV'))" | grep -q None
if [ $? -ne 0 ]; then
    echo "ERROR: Do not run this script inside Virtualenv. Type \`deactivate\` and run again.";
    exit 1;
fi
command -v python3
if [ $? -ne 0 ]; then
    echo "ERROR: install Python3 before running this script"
    exit 1
fi
VENV=$(mktemp -d)
python3 -m venv "$VENV"
source "$VENV"/bin/activate
pip install --quiet boto3 chalice docopt pyyaml jsonschema
export PYTHONPATH="$PYTHONPATH:$source_dir/lib/MediaInsightsEngineLambdaHelper/"
echo "PYTHONPATH=$PYTHONPATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install required Python libraries."
    exit 1
fi

echo "------------------------------------------------------------------------------"
echo "Create distribution directory"
echo "------------------------------------------------------------------------------"

# Setting up directories
echo "rm -rf $dist_dir"
rm -rf "$dist_dir"
# Create new dist directory
echo "mkdir -p $dist_dir"
mkdir -p "$dist_dir"

echo "------------------------------------------------------------------------------"
echo "Building MIEHelper package"
echo "------------------------------------------------------------------------------"

cd "$source_dir"/lib/MediaInsightsEngineLambdaHelper || exit 1
rm -rf build
rm -rf dist
rm -rf Media_Insights_Engine_Lambda_Helper.egg-info
python3 setup.py bdist_wheel > /dev/null
echo -n "Created: "
find "$source_dir"/lib/MediaInsightsEngineLambdaHelper/dist/
cd "$template_dir"/ || exit 1

echo "------------------------------------------------------------------------------"
echo "Building Lambda Layers"
echo "------------------------------------------------------------------------------"
# Build MediaInsightsEngineLambdaHelper Python package
cd "$template_dir"/lambda_layer_factory/ || exit 1
rm -f media_insights_engine_lambda_layer_python*.zip*
rm -f Media_Insights_Engine*.whl
cp -R "$source_dir"/lib/MediaInsightsEngineLambdaHelper .
cd MediaInsightsEngineLambdaHelper/ || exit 1
echo "Building MIE Lambda Helper python library"
python3 setup.py bdist_wheel > /dev/null
cp dist/*.whl ../
cp dist/*.whl "$source_dir"/lib/MediaInsightsEngineLambdaHelper/dist/
echo "MIE Lambda Helper python library is at $source_dir/lib/MediaInsightsEngineLambdaHelper/dist/"
cd "$source_dir"/lib/MediaInsightsEngineLambdaHelper/dist/ || exit 1
ls -1 "$(pwd)"/*.whl
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to build MIE Lambda Helper python library"
  exit 1
fi
cd "$template_dir"/lambda_layer_factory/ || exit 1
rm -rf MediaInsightsEngineLambdaHelper/
file=$(ls Media_Insights_Engine*.whl)
# Note, $(pwd) will be mapped to /packages/ in the Docker container used for building the Lambda zip files. We reference /packages/ in requirements.txt for that reason.
# Add the whl file to requirements.txt if it is not already there
mv requirements.txt requirements.txt.old
cat requirements.txt.old | grep -v "Media_Insights_Engine_Lambda_Helper" > requirements.txt
echo "/packages/$file" >> requirements.txt;
# Build Lambda layer zip files and rename them to the filenames expected by media-insights-stack.yaml. The Lambda layer build script runs in Docker.
# If Docker is not installed, then we'll use prebuilt Lambda layer zip files.
echo "Running build-lambda-layer.sh"
rm -rf lambda_layer-python-* lambda_layer-python*.zip
./build-lambda-layer.sh requirements.txt > /dev/null
if [ $? -eq 0 ]; then
  mv lambda_layer-python3.6.zip media_insights_engine_lambda_layer_python3.6.zip
  mv lambda_layer-python3.7.zip media_insights_engine_lambda_layer_python3.7.zip
  mv lambda_layer-python3.8.zip media_insights_engine_lambda_layer_python3.8.zip
  rm -rf lambda_layer-python-3.6/ lambda_layer-python-3.7/ lambda_layer-python-3.8/
  echo "Lambda layer build script completed.";
else
  echo "WARNING: Lambda layer build script failed. We'll use a pre-built Lambda layers instead.";
  s3domain="s3-$region.amazonaws.com"
  if [ "$region" = "us-east-1" ]; then
    s3domain="s3.amazonaws.com"
  fi
  echo "Downloading https://rodeolabz-$region.$s3domain/media_insights_engine/media_insights_engine_lambda_layer_python3.6.zip"
  wget -q https://rodeolabz-"$region"."$s3domain"/media_insights_engine/media_insights_engine_lambda_layer_python3.6.zip
  echo "Downloading https://rodeolabz-$region.$s3domain/media_insights_engine/media_insights_engine_lambda_layer_python3.7.zip"
  wget -q https://rodeolabz-"$region"."$s3domain"/media_insights_engine/media_insights_engine_lambda_layer_python3.7.zip
  echo "Downloading https://rodeolabz-$region.$s3domain/media_insights_engine/media_insights_engine_lambda_layer_python3.8.zip"
  wget -q https://rodeolabz-"$region"."$s3domain"/media_insights_engine/media_insights_engine_lambda_layer_python3.8.zip
fi
echo "Copying Lambda layer zips to $dist_dir:"
cp -v media_insights_engine_lambda_layer_python3.6.zip "$dist_dir"
cp -v media_insights_engine_lambda_layer_python3.7.zip "$dist_dir"
cp -v media_insights_engine_lambda_layer_python3.8.zip "$dist_dir"
mv requirements.txt.old requirements.txt
cd "$template_dir" || exit 1

echo "------------------------------------------------------------------------------"
echo "CloudFormation Templates"
echo "------------------------------------------------------------------------------"

echo "Preparing template files:"
cp "$workflows_dir/instant_translate.yaml" "$dist_dir/instant_translate.template"
cp "$workflows_dir/transcribe.yaml" "$dist_dir/transcribe.template"
cp "$workflows_dir/rekognition.yaml" "$dist_dir/rekognition.template"
cp "$workflows_dir/comprehend.yaml" "$dist_dir/comprehend.template"
cp "$workflows_dir/MieCompleteWorkflow.yaml" "$dist_dir/MieCompleteWorkflow.template"
cp "$source_dir/operators/operator-library.yaml" "$dist_dir/media-insights-operator-library.template"
cp "$template_dir/media-insights-stack.yaml" "$dist_dir/media-insights-stack.template"
cp "$template_dir/string.yaml" "$dist_dir/string.template"
cp "$template_dir/media-insights-test-operations-stack.yaml" "$dist_dir/media-insights-test-operations-stack.template"
cp "$template_dir/media-insights-dataplane-streaming-stack.template" "$dist_dir/media-insights-dataplane-streaming-stack.template"
cp "$workflows_dir/rekognition.yaml" "$dist_dir/rekognition.template"
cp "$workflows_dir/MieCompleteWorkflow.yaml" "$dist_dir/MieCompleteWorkflow.template"
cp "$source_dir/consumers/elastic/media-insights-elasticsearch.yaml" "$dist_dir/media-insights-elasticsearch.template"
cp "$source_dir/consumers/elastic/media-insights-elasticsearch.yaml" "$dist_dir/media-insights-s3.template"
cp "$webapp_dir/media-insights-webapp.yaml" "$dist_dir/media-insights-webapp.template"
find "$dist_dir"
echo "Updating code source bucket in template files with '$bucket'"
echo "Updating solution version in template files with '$version'"
new_bucket="s/%%BUCKET_NAME%%/$bucket/g"
new_version="s/%%VERSION%%/$version/g"
# Update templates in place. Copy originals to [filename].orig
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-stack.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-stack.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-operator-library.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-operator-library.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-test-operations-stack.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-test-operations-stack.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-dataplane-streaming-stack.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-dataplane-streaming-stack.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-elasticsearch.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-elasticsearch.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-s3.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-s3.template"
sed -i.orig -e "$new_bucket" "$dist_dir/media-insights-webapp.template"
sed -i.orig -e "$new_version" "$dist_dir/media-insights-webapp.template"

echo "------------------------------------------------------------------------------"
echo "Operators"
echo "------------------------------------------------------------------------------"

# ------------------------------------------------------------------------------"
# Operator Failed Lambda
# ------------------------------------------------------------------------------"

echo "Building 'operator failed' function"
cd "$source_dir/operators/operator_failed" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q dist/operator_failed.zip operator_failed.py
cp "./dist/operator_failed.zip" "$dist_dir/operator_failed.zip"

# ------------------------------------------------------------------------------"
# Mediainfo Operation
# ------------------------------------------------------------------------------"

echo "Building Mediainfo function"
cd "$source_dir/operators/mediainfo" || exit 1
# Make lambda package
[ -e dist ] && rm -r dist
mkdir -p dist
# Add the app code to the dist zip.
zip -q dist/mediainfo.zip mediainfo.py
# Zip is ready. Copy it to the distribution directory.
cp "./dist/mediainfo.zip" "$dist_dir/mediainfo.zip"

# ------------------------------------------------------------------------------"
# Mediaconvert Operations
# ------------------------------------------------------------------------------"

echo "Building Media Convert function"
cd "$source_dir/operators/mediaconvert" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q dist/start_media_convert.zip start_media_convert.py
zip -q dist/get_media_convert.zip get_media_convert.py
cp "./dist/start_media_convert.zip" "$dist_dir/start_media_convert.zip"
cp "./dist/get_media_convert.zip" "$dist_dir/get_media_convert.zip"

# ------------------------------------------------------------------------------"
# Thumbnail Operations
# ------------------------------------------------------------------------------"

echo "Building Thumbnail function"
cd "$source_dir/operators/thumbnail" || exit 1
# Make lambda package
[ -e dist ] && rm -r dist
mkdir -p dist
if ! [ -d ./dist/start_thumbnail.zip ]; then
  zip -q -r9 ./dist/start_thumbnail.zip .
elif [ -d ./dist/start_thumbnail.zip ]; then
  echo "Package already present"
fi
zip -q -g dist/start_thumbnail.zip start_thumbnail.py
cp "./dist/start_thumbnail.zip" "$dist_dir/start_thumbnail.zip"

if ! [ -d ./dist/check_thumbnail.zip ]; then
  zip -q -r9 ./dist/check_thumbnail.zip .
elif [ -d ./dist/check_thumbnail.zip ]; then
  echo "Package already present"
fi
zip -q -g dist/check_thumbnail.zip check_thumbnail.py
cp "./dist/check_thumbnail.zip" "$dist_dir/check_thumbnail.zip"

# ------------------------------------------------------------------------------"
# Transcribe Operations
# ------------------------------------------------------------------------------"

echo "Building Transcribe functions"
cd "$source_dir/operators/transcribe" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q -g ./dist/start_transcribe.zip ./start_transcribe.py
zip -q -g ./dist/get_transcribe.zip ./get_transcribe.py
cp "./dist/start_transcribe.zip" "$dist_dir/start_transcribe.zip"
cp "./dist/get_transcribe.zip" "$dist_dir/get_transcribe.zip"

# ------------------------------------------------------------------------------"
# Create Captions Operations
# ------------------------------------------------------------------------------"

echo "Building Stage completion function"
cd "$source_dir/operators/captions" || exit
[ -e dist ] && rm -r dist
mkdir -p dist
zip -g ./dist/get_captions.zip ./get_captions.py
cp "./dist/get_captions.zip" "$dist_dir/get_captions.zip"

# ------------------------------------------------------------------------------"
# Translate Operations
# ------------------------------------------------------------------------------"

echo "Building Translate function"
cd "$source_dir/operators/translate" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
[ -e package ] && rm -r package
mkdir -p package
echo "create requirements for lambda"
# Make lambda package
pushd package || exit 1
echo "create lambda package"
# Handle distutils install errors
touch ./setup.cfg
echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg
# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install --quiet -r ../requirements.txt --target .
elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install --quiet -r ../requirements.txt --target .
elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi
if ! [ -d ../dist/start_translate.zip ]; then
  zip -q -r9 ../dist/start_translate.zip .

elif [ -d ../dist/start_translate.zip ]; then
  echo "Package already present"
fi
popd || exit 1
zip -q -g ./dist/start_translate.zip ./start_translate.py
cp "./dist/start_translate.zip" "$dist_dir/start_translate.zip"

# ------------------------------------------------------------------------------"
# Polly operators
# ------------------------------------------------------------------------------"

echo "Building Polly function"
cd "$source_dir/operators/polly" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q -g ./dist/start_polly.zip ./start_polly.py
zip -q -g ./dist/get_polly.zip ./get_polly.py
cp "./dist/start_polly.zip" "$dist_dir/start_polly.zip"
cp "./dist/get_polly.zip" "$dist_dir/get_polly.zip"

# ------------------------------------------------------------------------------"
# Comprehend operators
# ------------------------------------------------------------------------------"

echo "Building Comprehend function"
cd "$source_dir/operators/comprehend" || exit 1

[ -e dist ] && rm -r dist
[ -e package ] && rm -r package
for dir in ./*;
  do
    echo "$dir"
    cd "$dir" || exit 1
    mkdir -p dist
    mkdir -p package
    echo "creating requirements for lambda"
    # Package dependencies listed in requirements.txt
    pushd package || exit 1
    # Handle distutils install errors with setup.cfg
    touch ./setup.cfg
    echo "[install]" > ./setup.cfg
    echo "prefix= " >> ./setup.cfg
    if [[ $dir == "./key_phrases" ]]; then
      if ! [ -d ../dist/start_key_phrases.zip ]; then
        zip -q -r9 ../dist/start_key_phrases.zip .
      elif [ -d ../dist/start_key_phrases.zip ]; then
        echo "Package already present"
      fi
      if ! [ -d ../dist/get_key_phrases.zip ]; then
        zip -q -r9 ../dist/get_key_phrases.zip .

      elif [ -d ../dist/get_key_phrases.zip ]; then
        echo "Package already present"
      fi
      popd || exit 1
      zip -q -g dist/start_key_phrases.zip start_key_phrases.py
      zip -q -g dist/get_key_phrases.zip get_key_phrases.py
      echo "$PWD"
      cp ./dist/start_key_phrases.zip "$dist_dir/start_key_phrases.zip"
      cp ./dist/get_key_phrases.zip "$dist_dir/get_key_phrases.zip"
      mv -f ./dist/*.zip "$dist_dir"
    elif [[ "$dir" == "./entities" ]]; then
      if ! [ -d ../dist/start_entity_detection.zip ]; then
      zip -q -r9 ../dist/start_entity_detection.zip .
      elif [ -d ../dist/start_entity_detection.zip ]; then
      echo "Package already present"
      fi
      if ! [ -d ../dist/get_entity_detection.zip ]; then
      zip -q -r9 ../dist/get_entity_detection.zip .
      elif [ -d ../dist/get_entity_detection.zip ]; then
      echo "Package already present"
      fi
      popd || exit 1
      echo "$PWD"
      zip -q -g dist/start_entity_detection.zip start_entity_detection.py
      zip -q -g dist/get_entity_detection.zip get_entity_detection.py
      mv -f ./dist/*.zip "$dist_dir"
    fi
    cd ..
  done;

# ------------------------------------------------------------------------------"
# Rekognition operators
# ------------------------------------------------------------------------------"

echo "Building Rekognition functions"
cd "$source_dir/operators/rekognition" || exit 1
# Make lambda package
echo "creating lambda packages"
# All the Python dependencies for Rekognition functions are in the Lambda layer, so
# we can deploy the zipped source file without dependencies.
zip -q -r9 generic_data_lookup.zip generic_data_lookup.py
zip -q -r9 start_celebrity_recognition.zip start_celebrity_recognition.py
zip -q -r9 check_celebrity_recognition_status.zip check_celebrity_recognition_status.py
zip -q -r9 start_content_moderation.zip start_content_moderation.py
zip -q -r9 check_content_moderation_status.zip check_content_moderation_status.py
zip -q -r9 start_face_detection.zip start_face_detection.py
zip -q -r9 check_face_detection_status.zip check_face_detection_status.py
zip -q -r9 start_face_search.zip start_face_search.py
zip -q -r9 check_face_search_status.zip check_face_search_status.py
zip -q -r9 start_label_detection.zip start_label_detection.py
zip -q -r9 check_label_detection_status.zip check_label_detection_status.py
zip -q -r9 start_person_tracking.zip start_person_tracking.py
zip -q -r9 check_person_tracking_status.zip check_person_tracking_status.py
zip -q -r9 start_text_detection.zip start_text_detection.py
zip -q -r9 check_text_detection_status.zip check_text_detection_status.py

mv -f ./*.zip "$dist_dir"

# ------------------------------------------------------------------------------"
# Test operators
# ------------------------------------------------------------------------------"

echo "Building test operators"
cd "$source_dir/operators/test" || exit
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q -g ./dist/test_operations.zip ./test.py
cp "./dist/test_operations.zip" "$dist_dir/test_operations.zip"

echo "------------------------------------------------------------------------------"
echo "DynamoDB Stream Function"
echo "------------------------------------------------------------------------------"

echo "Building DDB Stream function"
cd "$source_dir/dataplanestream" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
[ -e package ] && rm -r package
mkdir -p package
echo "preparing packages from requirements.txt"
# Package dependencies listed in requirements.txt
pushd package || exit 1
# Handle distutils install errors with setup.cfg
touch ./setup.cfg
echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg
# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install --quiet -r ../requirements.txt --target .
elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install --quiet -r ../requirements.txt --target .
elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi
zip -q -r9 ../dist/ddbstream.zip .
popd || exit 1

zip -q -g dist/ddbstream.zip ./*.py
cp "./dist/ddbstream.zip" "$dist_dir/ddbstream.zip"

echo "------------------------------------------------------------------------------"
echo "Elasticsearch consumer Function"
echo "------------------------------------------------------------------------------"

echo "Building Elasticsearch Consumer function"
cd "$source_dir/consumers/elastic" || exit 1

[ -e dist ] && rm -r dist
mkdir -p dist
[ -e package ] && rm -r package
mkdir -p package
echo "preparing packages from requirements.txt"
# Package dependencies listed in requirements.txt
pushd package || exit 1
# Handle distutils install errors with setup.cfg
touch ./setup.cfg
echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg
# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install --quiet -r ../requirements.txt --target .
elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install --quiet -r ../requirements.txt --target .
elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi
zip -q -r9 ../dist/esconsumer.zip .
popd || exit 1

zip -q -g dist/esconsumer.zip ./*.py
cp "./dist/esconsumer.zip" "$dist_dir/esconsumer.zip"

echo "------------------------------------------------------------------------------"
echo "Workflow Scheduler"
echo "------------------------------------------------------------------------------"

echo "Building Workflow scheduler"
cd "$source_dir/workflow" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
[ -e package ] && rm -r package
mkdir -p package
echo "preparing packages from requirements.txt"
# Package dependencies listed in requirements.txt
cd package || exit 1
# Handle distutils install errors with setup.cfg
touch ./setup.cfg
echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg
cd ..
# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install --quiet -r ./requirements.txt --target package/
elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install --quiet -r ./requirements.txt --target package/
elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi
cd package || exit 1
zip -q -r9 ../dist/workflow.zip .
cd ..
zip -q -g dist/workflow.zip ./*.py
cp "./dist/workflow.zip" "$dist_dir/workflow.zip"

echo "------------------------------------------------------------------------------"
echo "Workflow API Stack"
echo "------------------------------------------------------------------------------"

echo "Building Workflow Lambda function"
cd "$source_dir/workflowapi" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
if ! [ -x "$(command -v chalice)" ]; then
  echo 'Chalice is not installed. It is required for this solution. Exiting.'
  exit 1
fi
echo "running chalice..."
chalice package --merge-template external_resources.json dist
echo "...chalice done"
echo "cp ./dist/sam.json $dist_dir/media-insights-workflowapi-stack.template"
cp dist/sam.json "$dist_dir"/media-insights-workflowapi-stack.template
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to build workflow api template"
  exit 1
fi
echo "cp ./dist/deployment.zip $dist_dir/workflowapi.zip"
cp ./dist/deployment.zip "$dist_dir"/workflowapi.zip
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to build workflow api template"
  exit 1
fi
rm -f ./dist/*

echo "------------------------------------------------------------------------------"
echo "Dataplane API Stack"
echo "------------------------------------------------------------------------------"

echo "Building Dataplane Stack"
cd "$source_dir/dataplaneapi" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
if ! [ -x "$(command -v chalice)" ]; then
  echo 'Chalice is not installed. It is required for this solution. Exiting.'
  exit 1
fi
chalice package --merge-template external_resources.json dist
echo "cp ./dist/sam.json $dist_dir/media-insights-dataplane-api-stack.template"
cp dist/sam.json "$dist_dir"/media-insights-dataplane-api-stack.template
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to build dataplane api template"
  exit 1
fi
echo "cp ./dist/deployment.zip $dist_dir/dataplaneapi.zip"
cp ./dist/deployment.zip "$dist_dir"/dataplaneapi.zip
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to build dataplane api template"
  exit 1
fi
rm -f ./dist/*

echo "------------------------------------------------------------------------------"
echo "Demo website stack"
echo "------------------------------------------------------------------------------"

echo "Building website helper function"
cd "$webapp_dir/helper" || exit 1
[ -e dist ] && rm -r dist
mkdir -p dist
zip -q -g ./dist/websitehelper.zip ./website_helper.py
cp "./dist/websitehelper.zip" "$dist_dir/websitehelper.zip"

echo "Building Vue.js website"
cd "$webapp_dir/" || exit 1
echo "Installing node dependencies"
npm install
echo "Compiling the vue app"
npm run build
echo "Built demo webapp"

echo "------------------------------------------------------------------------------"
echo "Copy dist to S3"
echo "------------------------------------------------------------------------------"

echo "Copying the prepared distribution to S3..."
for file in "$dist_dir"/*.zip
do
  if [ -n "$profile" ]; then
    aws s3 cp "$file" s3://"$bucket"/media-insights-solution/"$version"/code/ --profile "$profile"
  else
    aws s3 cp "$file" s3://"$bucket"/media-insights-solution/"$version"/code/
  fi
done
for file in "$dist_dir"/*.template
do
  if [ -n "$profile" ]; then
    aws s3 cp "$file" s3://"$bucket"/media-insights-solution/"$version"/cf/ --profile "$profile"
  else
    aws s3 cp "$file" s3://"$bucket"/media-insights-solution/"$version"/cf/
  fi
done
echo "Uploading the MIE web app..."
if [ -n "$profile" ]; then
  aws s3 cp "$webapp_dir"/dist s3://"$bucket"/media-insights-solution/"$version"/code/website --recursive --profile "$profile"
else
  aws s3 cp "$webapp_dir"/dist s3://"$bucket"/media-insights-solution/"$version"/code/website --recursive
fi

echo "------------------------------------------------------------------------------"
echo "S3 packaging complete"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf "$VENV"

echo "------------------------------------------------------------------------------"
echo "Cleaning up complete"
echo "------------------------------------------------------------------------------"

echo ""
echo "Template to deploy:"
if [ "$region" == "us-east-1" ]; then
  echo https://"$bucket".s3.amazonaws.com/media-insights-solution/"$version"/cf/media-insights-stack.template
else
  echo https://"$bucket".s3."$region".amazonaws.com/media-insights-solution/"$version"/cf/media-insights-stack.template
fi

echo "------------------------------------------------------------------------------"
echo "Done"
echo "------------------------------------------------------------------------------"
