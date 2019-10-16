#!/bin/bash

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This assumes all of the OS-level configuration has been completed and git repo has already been cloned

# USAGE:
# cd deployment
# ./build-s3-dist.sh {SOURCE-BUCKET-BASE-NAME} {VERSION} {REGION} [PROFILE]
#   SOURCE-BUCKET-BASE-NAME should be the base name for the S3 bucket location where the template will source the Lambda code from.
#   VERSION should be in a format like v1.0.0
#   REGION needs to be in a format like us-east-1
#   PROFILE is optional. It's the profile  that you have setup in ~/.aws/config that you want to use for aws CLI commands. It defaults to "default"
#
# The template will append '-[region_name]' to this bucket name.
# For example: ./build-s3-dist.sh solutions
# The template will then expect the source code to be located in the solutions-[region_name] bucket

# Check to see if input has been provided:
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name,  version where the lambda code will eventually reside and the region of the deploy."
    echo "For example: ./build-s3-dist.sh solutions v1.0.0 us-east-1 default"
    exit 1
fi

bucket_basename=$1
version=$2
region=$3
bucket=$1-$3
profile="default"
if [ -n "$4" ]; then profile=$4; fi

# Check if region is supported:
if [ $region != "us-east-1" ] &&
   [ $region != "us-east-2" ] &&
   [ $region != "us-west-2" ] &&
   [ $region != "eu-west-1" ] &&
   [ $region != "ap-south-1" ] &&
   [ $region != "ap-northeast-1" ] &&
   [ $region != "ap-southheast-2" ] &&
   [ $region != "ap-northeast-2" ]; then
   echo "ERROR. Rekognition operatorions are not supported in region "$region
   exit 1
fi


# Build source S3 Bucket

# if [[ -d ~/.aws ]]; then

# echo "This script assumes your aws cli is setup correctly. Here is the config we have:"
# cat ~/.aws/config
# echo "Ensure this is the region you want to deploy too"
# echo "Please verify you have the correct access keys in your credentials file and iam permissions to create an s3 bucket"

# read -p "Is your AWS CLI Setup correctly? (y or yes to continue)"  confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1

# bucket="$1`date +%s`"
# echo "We are creating an s3 bucket named $bucket in your configured AWS account"

# aws s3 mb s3://$bucket/

# elif [[ ! -d ~/.aws ]]; then

# echo "This script requires the AWS CLI to be setup"

# exit 1

# fi



# Get reference for all important folders
template_dir="$PWD"
dist_dir="$template_dir/dist"
source_dir="$template_dir/../source"
workflows_dir="$template_dir/../source/workflows"
webapp_dir="$template_dir/../webapp"
transcriber_dir="$template_dir/../video-transcriber"


# Create and activate a temporary Python environment for this script.
echo "------------------------------------------------------------------------------"
echo "Creating a temporary Python virtualenv for this script"
echo "------------------------------------------------------------------------------"
python -c "import os; print (os.getenv('VIRTUAL_ENV'))" | grep -q None
if [ $? -ne 0 ]; then
    echo "ERROR: Do not run this script inside Virtualenv. Type \`deactivate\` and run again.";
    exit 1;
fi
which python3
if [ $? -ne 0 ]; then
    echo "ERROR: install Python3 before running this script"
    exit 1
fi
VENV=$(mktemp -d)
python3 -m venv $VENV
source $VENV/bin/activate
pip install boto3 chalice docopt aws-sam-translator pyyaml
#pip install git+ssh://git.amazon.com/pkg/MediaInsightsEngineLambdaHelper
export PYTHONPATH="$PYTHONPATH:$template_dir/../lib/MediaInsightsEngineLambdaHelper"
echo "PYTHONPATH=$PYTHONPATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install required Python libraries."
    exit 1
fi

echo "------------------------------------------------------------------------------"
echo "Build S3 Bucket"
echo "------------------------------------------------------------------------------"

echo "------------------------------------------------------------------------------"
echo "Rebuild distribution"
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
cd $template_dir/../lib/MediaInsightsEngineLambdaHelper
rm -rf build
rm -rf dist
rm -rf Media_Insights_Engine_Lambda_Helper.egg-info
python3 setup.py bdist_wheel

cd $template_dir/

echo "------------------------------------------------------------------------------"
echo "Building Lambda Layers"
echo "------------------------------------------------------------------------------"
# Build MediaInsightsEngineLambdaHelper Python package
cd $template_dir/lambda_layer_factory/
rm -f Media_Insights_Engine*.whl
# TODO: replace these whl build commands with pip install once LambdaHelper package is in Pypi
#git clone git+ssh://git.amazon.com/pkg/MediaInsightsEngineLambdaHelper
cp -R $template_dir/../lib/MediaInsightsEngineLambdaHelper .
cd MediaInsightsEngineLambdaHelper/
python3 setup.py bdist_wheel
cp dist/*.whl ../
cp dist/*.whl $template_dir/../lib/MediaInsightsEngineLambdaHelper/dist/
cd $template_dir/lambda_layer_factory/
rm -rf MediaInsightsEngineLambdaHelper/
file=$(ls Media_Insights_Engine*.whl)
# Note, $(pwd) will be mapped to packages/ in the Docker container used for building the Lambda zip files. We reference /packages/ in requirements.txt for that reason.
# Add the whl file to requirements.txt if it is not already there
mv requirements.txt requirements.txt.old
cat requirements.txt.old | grep -v "Media_Insights_Engine_Lambda_Helper" > requirements.txt
echo "/packages/$file" >> requirements.txt;
# Build Lambda layer zip files and rename them to the filenames expected by media-insights-stack.yaml. The Lambda layer build script runs in Docker.
# If Docker is not installed, then we'll use prebuilt Lambda layer zip files.
./build-lambda-layer.sh requirements.txt
if [ $? -eq 0 ]; then
    mv lambda_layer-python3.6.zip media_insights_engine_lambda_layer_python3.6.zip
    mv lambda_layer-python3.7.zip media_insights_engine_lambda_layer_python3.7.zip
    rm -rf lambda_layer-python-3.6/ lambda_layer-python-3.7/
else
    echo "WARNING: build-lambda-layer.sh failed. Proceeding to use a pre-built Lambda layer which may not include latest Python packages.";
    aws s3 cp s3://rodeolabz-$region/media_insights_engine/media_insights_engine_lambda_layer_python3.6.zip . --profile $profile
    aws s3 cp s3://rodeolabz-$region/media_insights_engine/media_insights_engine_lambda_layer_python3.7.zip . --profile $profile
fi
echo "Copying Lambda layer zips to $dist_dir:"
cp -v media_insights_engine_lambda_layer_python3.6.zip $dist_dir/
cp -v media_insights_engine_lambda_layer_python3.7.zip $dist_dir/
mv requirements.txt.old requirements.txt
cd $template_dir/

echo "------------------------------------------------------------------------------"
echo "Copy CloudFormation Templates"
echo "------------------------------------------------------------------------------"

# Instant Translate template
echo "Copying instant translate template to dist directory"
echo "cp $workflows_dir/instant_translate.yaml $dist_dir/instant_translate.template"
cp "$workflows_dir/instant_translate.yaml" "$dist_dir/instant_translate.template"

# Transcribe template
echo "Copying transcribe template to dist directory"
echo "cp $workflows_dir/transcribe.yaml $dist_dir/transcribe.template"
cp "$workflows_dir/transcribe.yaml" "$dist_dir/transcribe.template"

# Rekognition template
echo "Copying rekognition template to dist directory"
echo "cp $workflows_dir/rekognition.yaml $dist_dir/rekognition.template"
cp "$workflows_dir/rekognition.yaml" "$dist_dir/rekognition.template"

# Comprehend template
echo "Copying comprehend template to dist directory"
echo "cp $workflows_dir/comprehend.yaml $dist_dir/comprehend.template"
cp "$workflows_dir/comprehend.yaml" "$dist_dir/comprehend.template"

# Kitchen Sink template
echo "Copying comprehend template to dist directory"
echo "cp $workflows_dir/MieCompleteWorkflow.yaml $dist_dir/MieCompleteWorkflow.template"
cp "$workflows_dir/MieCompleteWorkflow.yaml" "$dist_dir/MieCompleteWorkflow.template"

# Operator library template
echo "Copying operator library template to dist directory"
echo "cp $source_dir/operators/operator-library.yaml $dist_dir/media-insights-operator-library.template"
cp "$source_dir/operators/operator-library.yaml" "$dist_dir/media-insights-operator-library.template"

echo "Updating code source bucket in operator library template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-operator-library.template"
sed -i '' -e $replace "$dist_dir/media-insights-operator-library.template"

echo "Replacing solution version in operator library template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-operator-library.template"
sed -i '' -e $replace "$dist_dir/media-insights-operator-library.template"


# Workflow template
echo "Copying workflow template to dist directory"
echo "cp $template_dir/media-insights-stack.yaml $dist_dir/media-insights-stack.template"
cp "$template_dir/media-insights-stack.yaml" "$dist_dir/media-insights-stack.template"

echo "Updating code source bucket in workflow template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-stack.template"

echo "Replacing solution version in template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-stack.template"

# Operations template
echo "Copying operations template to dist directory"
echo "cp $template_dir/media-insights-test-operations-stack.yaml $dist_dir/media-insights-test-operations-stack.template"
cp "$template_dir/media-insights-test-operations-stack.yaml" "$dist_dir/media-insights-test-operations-stack.template"

echo "Updating code source bucket in operations template with '$bucket_basename'"
replace="s/%%BUCKET_NAME%%/$bucket_basename/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-test-operations-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-test-operations-stack.template"

echo "Replacing solution version in template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-test-operations-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-test-operations-stack.template"

# Analytics Pipeline template
echo "Copying analytics pipeline template to dist directory"
cp "$template_dir/media-insights-dataplane-streaming-stack.template" "$dist_dir/media-insights-dataplane-streaming-stack.template"
echo "Updating code source bucket in analytics pipeline template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-dataplane-streaming-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-dataplane-streaming-stack.template"

echo "Replacing solution version in analytics pipeline consumer template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-dataplane-streaming-stack.template"
sed -i '' -e $replace "$dist_dir/media-insights-dataplane-streaming-stack.template"


# Elasticsearch consumer template
echo "Copying Elasticsearch consumer template to dist directory"
cp "$source_dir/consumers/elastic/media-insights-elasticsearch.yaml" "$dist_dir/media-insights-elasticsearch.template"
echo "Updating code source bucket in Elasticsearch consumer template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-elasticsearch.template"
sed -i '' -e $replace "$dist_dir/media-insights-elasticsearch.template"

echo "Replacing solution version in Elasticsearch consumer template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-elasticsearch.template"
sed -i '' -e $replace "$dist_dir/media-insights-elasticsearch.template"

# S3 consumer template
echo "Copying S3 consumer template to dist directory"
cp "$source_dir/consumers/s3/media-insights-s3.yaml" "$dist_dir/media-insights-s3.template"

# Website template

echo "Copying Demo Website template to dist directory"
cp "$webapp_dir/media-insights-webapp.yaml" "$dist_dir/media-insights-webapp.template"

echo "Updating code source bucket in Demo Website template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-webapp.template"
sed -i '' -e $replace "$dist_dir/media-insights-webapp.template"

echo "Replacing solution version in Demo Website template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/media-insights-webapp.template"
sed -i '' -e $replace "$dist_dir/media-insights-webapp.template"

# Transcriber template

echo "Copying Transcriber App template to dist directory"
cp "$transcriber_dir/cloudformation/transcriber-webapp.yaml" "$dist_dir/transcriber-webapp.template"

echo "Updating code source bucket in Trancriber App template with '$bucket'"
replace="s/%%BUCKET_NAME%%/$bucket/g"
echo "sed -i '' -e $replace $dist_dir/transcriber-webapp.template"
sed -i '' -e $replace "$dist_dir/transcriber-webapp.template"

echo "Replacing solution version in Transcriber App template with '$2'"
replace="s/%%VERSION%%/$2/g"
echo "sed -i '' -e $replace $dist_dir/transcriber-webapp.template"
sed -i '' -e $replace "$dist_dir/transcriber-webapp.template"

echo "------------------------------------------------------------------------------"
echo "Operator failed  lambda"
echo "------------------------------------------------------------------------------"

echo "Building operator failed function"
cd "$source_dir/operators/operator_failed" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/operator_failed.zip ]; then
  zip -r9 ../dist/operator_failed.zip .

elif [ -d ../dist/operator_failed.zip ]; then
  echo "Package already present"
fi

popd

zip -g dist/operator_failed.zip operator_failed.py

cp "./dist/operator_failed.zip" "$dist_dir/operator_failed.zip"

echo "------------------------------------------------------------------------------"
echo "Mediaconvert  Operations"
echo "------------------------------------------------------------------------------"

echo "Building Media Convert function"
cd "$source_dir/operators/mediaconvert" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/start_media_convert.zip ]; then
  zip -r9 ../dist/start_media_convert.zip .

elif [ -d ../dist/start_media_convert.zip ]; then
  echo "Package already present"
fi

if ! [ -d ../dist/get_media_convert.zip ]; then
  zip -r9 ../dist/get_media_convert.zip .

elif [ -d ../dist/get_media_convert.zip ]; then
  echo "Package already present"
fi

popd

zip -g dist/start_media_convert.zip start_media_convert.py awsmie.py
zip -g dist/get_media_convert.zip get_media_convert.py awsmie.py

cp "./dist/start_media_convert.zip" "$dist_dir/start_media_convert.zip"
cp "./dist/get_media_convert.zip" "$dist_dir/get_media_convert.zip"

echo "------------------------------------------------------------------------------"
echo "Transcribe  Operations"
echo "------------------------------------------------------------------------------"

echo "Building Transcribe functions"
cd "$source_dir/operators/transcribe" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/start_transcribe.zip ]; then
  zip -r9 ../dist/start_transcribe.zip .

elif [ -d ../dist/start_transcribe.zip ]; then
  echo "Package already present"
fi

if ! [ -d ../dist/get_transcribe.zip ]; then
  zip -r9 ../dist/get_transcribe.zip .

elif [ -d ../dist/get_transcribe.zip ]; then
  echo "Package already present"
fi

popd

zip -g dist/start_transcribe.zip start_transcribe.py awsmie.py
zip -g dist/get_transcribe.zip get_transcribe.py awsmie.py

cp "./dist/start_transcribe.zip" "$dist_dir/start_transcribe.zip"
cp "./dist/get_transcribe.zip" "$dist_dir/get_transcribe.zip"

echo "------------------------------------------------------------------------------"
echo "Create Captions Operations"
echo "------------------------------------------------------------------------------"

echo "Building Stage completion function"
cd "$source_dir/operators/captions" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/get_captions.zip ]; then
  zip -r9 ../dist/get_captions.zip .

elif [ -d ../dist/get_captions.zip ]; then
  echo "Package already present"
fi

popd

zip -g dist/get_captions.zip get_captions.py awsmie.py

cp "./dist/get_captions.zip" "$dist_dir/get_captions.zip"

echo "------------------------------------------------------------------------------"
echo "Translate  Operations"
echo "------------------------------------------------------------------------------"

echo "Building Translate function"
cd "$source_dir/operators/translate" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/start_translate.zip ]; then
  zip -r9 ../dist/start_translate.zip .

elif [ -d ../dist/start_translate.zip ]; then
  echo "Package already present"
fi

popd

zip -g dist/start_translate.zip start_translate.py awsmie.py

cp "./dist/start_translate.zip" "$dist_dir/start_translate.zip"

echo "------------------------------------------------------------------------------"
echo "Polly  operators"
echo "------------------------------------------------------------------------------"

echo "Building Polly function"
cd "$source_dir/operators/polly" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/start_polly.zip ]; then
  zip -r9 ../dist/start_polly.zip .

elif [ -d ../dist/start_polly.zip ]; then
  echo "Package already present"
fi

if ! [ -d ../dist/get_polly.zip ]; then
  zip -r9 ../dist/get_polly.zip .

elif [ -d ../dist/get_polly.zip ]; then
  echo "Package already present"
fi


popd

zip -g dist/start_polly.zip start_polly.py awsmie.py
zip -g dist/get_polly.zip get_polly.py awsmie.py

cp "./dist/start_polly.zip" "$dist_dir/start_polly.zip"
cp "./dist/get_polly.zip" "$dist_dir/get_polly.zip"

echo "------------------------------------------------------------------------------"
echo "Comprehend  operators"
echo "------------------------------------------------------------------------------"

echo "Building Comprehend function"
cd "$source_dir/operators/comprehend" || exit

[ -e dist ] && rm -r dist
[ -e package ] && rm -r package
for dir in ./*;
    do
        echo $dir
        cd $dir
        mkdir -p dist
        mkdir -p package

        echo "create requirements for lambda"

        #pipreqs . --force

        # Make lambda package

        pushd package
        echo "create lambda package"

        # Handle     distutils install errors

        touch ./setup.cfg

        echo "[install]" > ./setup.cfg
        echo "prefix= " >> ./setup.cfg

        if [[ $dir == "./key_phrases" ]]; then
            if ! [ -d ../dist/start_key_phrases.zip ]; then
              zip -r9 ../dist/start_key_phrases.zip .

            elif [ -d ../dist/start_key_phrases.zip ]; then
              echo "Package already present"
            fi

            if ! [ -d ../dist/get_key_phrases.zip ]; then
              zip -r9 ../dist/get_key_phrases.zip .

            elif [ -d ../dist/get_key_phrases.zip ]; then
              echo "Package already present"
            fi

            popd

            zip -g dist/start_key_phrases.zip start_key_phrases.py
            zip -g dist/get_key_phrases.zip get_key_phrases.py

            echo `pwd`

            cp ./dist/start_key_phrases.zip "$dist_dir/start_key_phrases.zip"
            cp ./dist/get_key_phrases.zip "$dist_dir/get_key_phrases.zip"

            mv -f ./dist/*.zip $dist_dir/

         elif [[ $dir == "./entities" ]]; then
            if ! [ -d ../dist/start_entity_detection.zip ]; then
            zip -r9 ../dist/start_entity_detection.zip .

            elif [ -d ../dist/start_entity_detection.zip ]; then
            echo "Package already present"
            fi

            if ! [ -d ../dist/get_entity_detection.zip ]; then
            zip -r9 ../dist/get_entity_detection.zip .

            elif [ -d ../dist/get_entity_detection.zip ]; then
            echo "Package already present"
            fi

            popd

            echo `pwd`

            zip -g dist/start_entity_detection.zip start_entity_detection.py
            zip -g dist/get_entity_detection.zip get_entity_detection.py

            mv -f ./dist/*.zip $dist_dir/

        fi

        cd ..
     done;

echo "------------------------------------------------------------------------------"
echo "Rekognition  operators"
echo "------------------------------------------------------------------------------"

echo "Building Rekognition functions"
cd "$source_dir/operators/rekognition" || exit

# Make lambda package

echo "create lambda package"

# All the Python dependencies for Rekognition functions are in the Lambda layer, so
# we can deploy the zipped source file without dependencies.

zip -r9 generic_data_lookup.zip generic_data_lookup.py
zip -r9 start_celebrity_recognition.zip start_celebrity_recognition.py
zip -r9 check_celebrity_recognition_status.zip check_celebrity_recognition_status.py
zip -r9 start_content_moderation.zip start_content_moderation.py
zip -r9 check_content_moderation_status.zip check_content_moderation_status.py
zip -r9 start_face_detection.zip start_face_detection.py
zip -r9 check_face_detection_status.zip check_face_detection_status.py
zip -r9 start_face_search.zip start_face_search.py
zip -r9 check_face_search_status.zip check_face_search_status.py
zip -r9 start_label_detection.zip start_label_detection.py
zip -r9 check_label_detection_status.zip check_label_detection_status.py
zip -r9 start_person_tracking.zip start_person_tracking.py
zip -r9 check_person_tracking_status.zip check_person_tracking_status.py

mv -f *.zip $dist_dir/

echo "------------------------------------------------------------------------------"
echo "DDB Stream Function"
echo "------------------------------------------------------------------------------"

echo "Building DDB Stream function"
cd "$source_dir/dataplanestream" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "Create requirements for lambda"

#pipreqs . --force

# Make lambda package
pushd package
echo "Create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi

zip -r9 ../dist/ddbstream.zip .

popd

zip -g dist/ddbstream.zip *.py

cp "./dist/ddbstream.zip" "$dist_dir/ddbstream.zip"

echo "------------------------------------------------------------------------------"
echo "Elasticsearch consumer Function"
echo "------------------------------------------------------------------------------"

echo "Building Elasticsearch Consumer function"
cd "$source_dir/consumers/elastic" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "Create requirements for lambda"

#pipreqs . --force

# Make lambda package
pushd package
echo "Create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi

zip -r9 ../dist/esconsumer.zip .

popd

zip -g dist/esconsumer.zip *.py

cp "./dist/esconsumer.zip" "$dist_dir/esconsumer.zip"


echo "------------------------------------------------------------------------------"
echo "Stage Completion Function"
echo "------------------------------------------------------------------------------"

echo "Building Stage completion function"
cd "$source_dir/workflow" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "Create requirements for lambda"

#pipreqs . --force

# Make lambda package
pushd package
echo "Create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi

zip -r9 ../dist/workflow.zip .

popd

zip -g dist/workflow.zip *.py

cp "./dist/workflow.zip" "$dist_dir/workflow.zip"

echo "------------------------------------------------------------------------------"
echo "Demo website helper Function"
echo "------------------------------------------------------------------------------"

echo "Building Demo website helper function"
cd "$webapp_dir/helper" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "Create requirements for lambda"

#pipreqs . --force

# Make lambda package
pushd package
echo "Create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi

zip -r9 ../dist/websitehelper.zip .

popd

zip -g dist/websitehelper.zip *.py

cp "./dist/websitehelper.zip" "$dist_dir/websitehelper.zip"

#echo "------------------------------------------------------------------------------"
#echo "Transcriber App Lambdas"
#echo "------------------------------------------------------------------------------"
#
#echo "Building Transcriber App Lambdas"
#cd "$transcriber_dir/lambda" || exit
#
#[ -e dist ] && rm -r dist
#mkdir -p dist
#
#[ -e package ] && rm -r package
#mkdir -p package
#
#echo "Create requirements for lambda"
#
##pipreqs . --force
#
## Make lambda package
#pushd package
#echo "Create lambda package"
#
## Handle distutils install errors
#
#touch ./setup.cfg
#
#echo "[install]" > ./setup.cfg
#echo "prefix= " >> ./setup.cfg
#
## Try and handle failure if pip version mismatch
#if [ -x "$(command -v pip)" ]; then
#  pip install -r ../requirements.txt --target .
#
#elif [ -x "$(command -v pip3)" ]; then
#  echo "pip not found, trying with pip3"
#  pip3 install -r ../requirements.txt --target .
#
#elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
#  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
#  exit 1
#fi
#
#zip -r9 ../dist/transcriberapp.zip .
#
#popd
#
#zip -rg dist/transcriberapp.zip *.js ../node_modules ../package.json
#
#cp "./dist/transcriberapp.zip" "$dist_dir/transcriberapp.zip"
#
#echo "------------------------------------------------------------------------------"
#echo "Transcriber App Lambda Layer"
#echo "------------------------------------------------------------------------------"
#
#echo "Building Transcriber App Lambda Layer"
#cd "$transcriber_dir/" || exit
#
#npm i
#
#[ -e dist ] && rm -r dist
#mkdir -p dist
#
#[ -e package ] && rm -r package
#mkdir -p package
#
#echo "Create requirements for lambda"
#
##pipreqs . --force
#
## Make lambda package
#pushd package
#echo "Create lambda package"
#
## Handle distutils install errors
#
#touch ./setup.cfg
#
#echo "[install]" > ./setup.cfg
#echo "prefix= " >> ./setup.cfg
#
## Try and handle failure if pip version mismatch
#if [ -x "$(command -v pip)" ]; then
#  pip install -r ../requirements.txt --target .
#
#elif [ -x "$(command -v pip3)" ]; then
#  echo "pip not found, trying with pip3"
#  pip3 install -r ../requirements.txt --target .
#
#elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
#  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
#  exit 1
#fi
#
#zip -r9 ../dist/transcriber-lambda-layer.zip .
#
#popd
#
#zip -rg dist/transcriber-lambda-layer.zip node_modules/ package.json
#
#cp "./dist/transcriber-lambda-layer.zip" "$dist_dir/transcriber-lambda-layer.zip"
#

echo "------------------------------------------------------------------------------"
echo "Workflow API Function"
echo "------------------------------------------------------------------------------"
echo "Building Workflow Lambda function"
cd "$source_dir/workflowapi" || exit

prefix="media-insights-solution/$2/code"


[ -e dist ] && rm -r dist
mkdir -p dist

if ! [ -x "$(command -v chalice)" ]; then
  echo 'Chalice is not installed. It is required for this solution. Exiting.'
  exit 1
fi


chalice package --merge-template external_resources.json dist
#./chalice-fix-inputs.py
#aws cloudformation package --template-file dist/sam.json --s3-bucket $bucket --s3-prefix $prefix --output-template-file "dist/workflowapi_sam.yaml" --profile $profile

# Need to add something here to ensure docopt and aws-sam-translator are present
./sam-translate.py --profile=$profile

echo "cp ./dist/workflowapi.json $dist_dir/media-insights-workflowapi-stack.template"
cp dist/workflowapi.json $dist_dir/media-insights-workflowapi-stack.template

echo "cp ./dist/deployment.zip $dist_dir/workflowapi.zip"
cp ./dist/deployment.zip $dist_dir/workflowapi.zip


echo "------------------------------------------------------------------------------"
echo "Dataplane API Stack"
echo "------------------------------------------------------------------------------"
echo "Building Dataplane Stack"
cd "$source_dir/dataplaneapi" || exit

prefix="media-insights-solution/$2/code"

[ -e dist ] && rm -r dist
mkdir -p dist

if ! [ -x "$(command -v chalice)" ]; then
  echo 'Chalice is not installed. It is required for this solution. Exiting.'
  exit 1
fi


chalice package --merge-template external_resources.json dist
#./chalice-fix-inputs.py
#aws cloudformation package --template-file dist/transformed_sam.json --s3-bucket $bucket --s3-prefix $prefix --output-template-file "dist/dataplaneapi_sam.yaml" --profile $profile

# Need to add something here to ensure docopt and aws-sam-translator are present
./sam-translate.py --profile=$profile


echo "cp ./dist/dataplaneapi.json $dist_dir/media-insights-dataplane-api-stack.template"
cp dist/dataplaneapi.json $dist_dir/media-insights-dataplane-api-stack.template


echo "cp ./dist/deployment.zip $dist_dir/dataplaneapi.zip"
cp ./dist/deployment.zip $dist_dir/dataplaneapi.zip


echo "------------------------------------------------------------------------------"
echo "Test operators"
echo "------------------------------------------------------------------------------"

echo "Building test operators"
cd "$source_dir/operators/test" || exit

[ -e dist ] && rm -r dist
mkdir -p dist

[ -e package ] && rm -r package
mkdir -p package

echo "create requirements for lambda"

#pipreqs . --force

# Make lambda package

pushd package
echo "create lambda package"

# Handle distutils install errors

touch ./setup.cfg

echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg

# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install -r ../requirements.txt --target .

elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install -r ../requirements.txt --target .

elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
 echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
 exit 1
fi

if ! [ -d ../dist/test_operations.zip ]; then
  echo "test_operations.zip zip file doesn't exist"
  zip -r9 ../dist/test_operations.zip .

elif [ -d ../dist/test_operations.zip ]; then
  echo "test_operations.zip Package already present"

fi

popd

zip -g dist/test_operations.zip *.py

echo "copy echo test_operations.zip to dist_dir"
cp "./dist/test_operations.zip" "$dist_dir/test_operations.zip"

echo "------------------------------------------------------------------------------"
echo "Build vue website "
echo "------------------------------------------------------------------------------"

cd "$webapp_dir/" || exit

echo "Installing node dependencies"

npm i

echo "Compiling the vue app"

npm run build

echo "Built demo webapp"

echo "------------------------------------------------------------------------------"
echo "Copy dist to S3"
echo "------------------------------------------------------------------------------"

echo "We are copying your source into the S3 bucket"

for file in $dist_dir/*.zip
do
     echo $file
     aws s3 cp $file s3://$bucket/media-insights-solution/$2/code/ --profile $profile
 done

 for file in $dist_dir/*.template
 do
     echo $file
     aws s3 cp $file s3://$bucket/media-insights-solution/$2/cf/ --profile $profile
 done

echo "We are uploading the MIE web app"

aws s3 cp $webapp_dir/dist s3://$bucket/media-insights-solution/$2/code/website --recursive --profile $profile
aws s3 cp $webapp_dir/.env s3://$bucket/media-insights-solution/$2/code/website/.env --profile $profile

#echo "We are uploading the transcriber web app"
#aws s3 cp $transcriber_dir/web s3://$bucket/media-insights-solution/$2/code/transcriberwebsite --recursive --profile $profile

echo "------------------------------------------------------------------------------"
echo "S3 Packaging Complete"
echo "------------------------------------------------------------------------------"


echo "------------------------------------------------------------------------------"
echo "Cleaning up"
echo "------------------------------------------------------------------------------"

# Deactivate and remove the temporary python virtualenv used to run this script
deactivate
rm -rf $VENV

echo "------------------------------------------------------------------------------"
echo "Done"
echo "------------------------------------------------------------------------------"
