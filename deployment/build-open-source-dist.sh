#!/bin/bash
###############################################################################
# DO NOT MODIFY THIS FILE.
# This file is used by the build pipeline for the [MIE solution](https://aws.amazon.com/solutions/implementations/aws-media-insights-engine/).
###############################################################################
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-s3-dist.sh solution-name
#
# Paramenters:
#  - solution-name: name of the solution for consistency

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the trademark approved solution name for the open source package."
    echo "For example: ./build-s3-dist.sh trademarked-solution-name"
    exit 1
fi

# Get reference for all important folders
orig_template_dir="$PWD"
orig_source_dir="$orig_template_dir/../source"
dist_dir="$orig_template_dir/open-source/"$1""
dist_template_dir="$dist_dir/deployment"
dist_source_dir="$dist_dir/source"

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old open-source folder"
echo "------------------------------------------------------------------------------"
echo "rm -rf $dist_dir/"
rm -rf "$dist_dir"/
echo "rm -rf $dist_dir/../$1.zip"
rm -f "$dist_dir"/../"$1".zip
echo "mkdir -p $dist_dir"
mkdir -p "$dist_dir"
echo "mkdir -p $dist_template_dir"
mkdir -p "$dist_template_dir"
echo "mkdir -p $dist_source_dir"
mkdir -p "$dist_source_dir"

echo "------------------------------------------------------------------------------"
echo "[Packing] Templates"
echo "------------------------------------------------------------------------------"
echo "copy yaml templates"
cp "$orig_template_dir"/*.yaml "$dist_template_dir"/

echo "------------------------------------------------------------------------------"
echo "[Packing] Build Script"
echo "------------------------------------------------------------------------------"
echo "cp $orig_template_dir/build-s3-dist.sh $dist_template_dir"
cp "$orig_template_dir"/build-s3-dist.sh "$dist_template_dir"

echo "------------------------------------------------------------------------------"
echo "[Packing] Source Folder"
echo "------------------------------------------------------------------------------"
echo "cp -R $orig_source_dir/* $dist_source_dir/"
cp -R "$orig_source_dir"/* "$dist_source_dir"/

echo "------------------------------------------------------------------------------"
echo "[Packing] Documentation"
echo "------------------------------------------------------------------------------"
echo "cp -R $orig_template_dir/../doc $dist_dir"
cp -R $orig_template_dir/../doc $dist_dir
echo "cp $orig_template_dir/../LICENSE.txt $dist_dir"
cp $orig_template_dir/../LICENSE.txt $dist_dir
echo "cp $orig_template_dir/../NOTICE.txt $dist_dir"
cp $orig_template_dir/../NOTICE.txt $dist_dir
echo "cp $orig_template_dir/../README.md $dist_dir"
cp $orig_template_dir/../README.md $dist_dir
echo "cp $orig_template_dir/../CODE_OF_CONDUCT.md $dist_dir"
cp $orig_template_dir/../CODE_OF_CONDUCT.md $dist_dir
echo "cp $orig_template_dir/../CONTRIBUTING.md $dist_dir"
cp $orig_template_dir/../CONTRIBUTING.md $dist_dir
echo "cp $orig_template_dir/../CHANGELOG.md $dist_dir"
cp $orig_template_dir/../CHANGELOG.md $dist_dir

echo "------------------------------------------------------------------------------"
echo "[Packing] Remove compiled python and node.js files"
echo "------------------------------------------------------------------------------"
echo "find $dist_dir -iname "dist" -type d -exec rm -rf "{}" \; 2> /dev/null"
find $dist_dir -iname "dist" -type d -exec rm -rf "{}" \; 2> /dev/null
echo "find $dist_dir -iname "package" -type d -exec rm -rf "{}" \; 2> /dev/null"
find $dist_dir -iname "package" -type d -exec rm -rf "{}" \; 2> /dev/null
echo "find $dist_dir -iname "__pycache__" -type d -exec rm -rf "{}" \; 2> /dev/null"
find $dist_dir -iname "__pycache__" -type d -exec rm -rf "{}" \; 2> /dev/null
echo "find $dist_dir -iname "node_modules" -type d -exec rm -rf "{}" \; 2> /dev/null"
find $dist_dir -iname "node_modules" -type d -exec rm -rf "{}" \; 2> /dev/null
echo "find $dist_dir -iname "deployments" -type d -exec rm -rf "{}" \; 2> /dev/null"
find $dist_dir -iname "deployments" -type d -exec rm -rf "{}" \; 2> /dev/null
echo "find ../ -type f -name 'package-lock.json' -delete"
find $dist_dir -type f -name 'package-lock.json' -delete

echo "------------------------------------------------------------------------------"
echo "[Packing] Clean library and lambda layer folders"
echo "------------------------------------------------------------------------------"

echo 'rm -rf "$dist_dir"/source/lib/MediaInsightsEngineLambdaHelper/build'
rm -rf "$dist_dir"/source/lib/MediaInsightsEngineLambdaHelper/build
echo 'rm -rf "$dist_dir"/orig_source_dir/lib/MediaInsightsEngineLambdaHelper/Media_Insights_Engine_Lambda_Helper.egg-info'
rm -rf "$dist_dir"/source/lib/MediaInsightsEngineLambdaHelper/Media_Insights_Engine_Lambda_Helper.egg-info
echo 'rm -f "$dist_dir"/source/lambda_layer_factory/media_insights_engine_lambda_layer_python*.zip*'
rm -f "$dist_dir"/source/lambda_layer_factory/media_insights_engine_lambda_layer_python*.zip*
echo 'rm -f "$dist_dir"/source/lambda_layer_factory/Media_Insights_Engine*.whl'
rm -f "$dist_dir"/source/lambda_layer_factory/Media_Insights_Engine*.whl
echo 'rm -rf "$dist_dir"/source/lambda_layer_factory/MediaInsightsEngineLambdaHelper'
rm -rf "$dist_dir"/source/lambda_layer_factory/MediaInsightsEngineLambdaHelper

echo "------------------------------------------------------------------------------"
echo "[Packing] Create GitHub (open-source) zip file"
echo "------------------------------------------------------------------------------"
echo "cd $dist_dir"
cd $dist_dir/../
echo "zip -q -r9 ./$1.zip $1"
zip -q -r9 ./"$1".zip "$1"
echo "Clean up open-source folder"
echo "rm -rf $1"
rm -rf "$1"
echo "Completed building $1.zip dist"
