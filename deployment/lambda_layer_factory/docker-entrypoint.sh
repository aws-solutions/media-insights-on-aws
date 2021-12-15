#!/bin/bash

echo "================================================================================"
echo "Installing the packages listed in requirements.txt:"
echo "================================================================================"
cat /packages/requirements.txt
pip3.8 install -q -r /packages/requirements.txt -t /packages/lambda_layer-python-3.8/python/lib/python3.8/site-packages
pip3.7 install -q -r /packages/requirements.txt -t /packages/lambda_layer-python-3.7/python/lib/python3.7/site-packages
pip3.6 install -q -r /packages/requirements.txt -t /packages/lambda_layer-python-3.6/python/lib/python3.6/site-packages

echo "================================================================================"
echo "Installing MediaInfo package"
echo "================================================================================"
# MediaInfo version 19.09 works but 20.03 does not. So, hardcoding to 19.09 instead of latest.
#VERSION=$(curl -s https://github.com/MediaArea/MediaInfoLib/releases/latest | cut -d "\"" -f 2 | awk -F "/" '{print $NF}' | tr -d 'v')
VERSION="19.09"
echo "MediaInfo latest version = v$VERSION"
URL=https://mediaarea.net/download/binary/libmediainfo0/${VERSION}/MediaInfo_DLL_${VERSION}_GNU_FromSource.tar.gz
echo "Downloading MediaInfo from $URL"
cd /
curl $URL -o mediainfo.tgz || exit 1
echo "Checking md5sum for MediaInfo source..."
# Check the md5sum for MediaInfo 19.09:
echo "74d33c37a161dba72baf09ad90c1c6b9  mediainfo.tgz" > mediainfo.md5 
md5sum --check mediainfo.md5 || exit 1
tar -xzf mediainfo.tgz
echo "Compiling MediaInfo library..."
cd MediaInfo_DLL_GNU_FromSource/
./SO_Compile.sh > /dev/null
echo "Finished building MediaInfo library files:"
find /MediaInfo_DLL_GNU_FromSource/MediaInfoLib/Project/GNU/Library/.libs/
cp /MediaInfo_DLL_GNU_FromSource/MediaInfoLib/Project/GNU/Library/.libs/* /packages/lambda_layer-python-3.6/python/ || exit 1
cp /MediaInfo_DLL_GNU_FromSource/MediaInfoLib/Project/GNU/Library/.libs/* /packages/lambda_layer-python-3.7/python/ || exit 1
cp /MediaInfo_DLL_GNU_FromSource/MediaInfoLib/Project/GNU/Library/.libs/* /packages/lambda_layer-python-3.8/python/ || exit 1

echo "================================================================================"
echo "Creating zip files for Lambda layers"
echo "================================================================================"
cd /packages/lambda_layer-python-3.8/
zip -q -r /packages/lambda_layer-python3.8.zip .
cd /packages/lambda_layer-python-3.7/
zip -q -r /packages/lambda_layer-python3.7.zip .
cd /packages/lambda_layer-python-3.6/
zip -q -r /packages/lambda_layer-python3.6.zip .

# Clean up build environment
cd /packages/
rm -rf /packages/pymediainfo-3.7/
rm -rf /packages/pymediainfo-3.8/
rm -rf /packages/lambda_layer-python-3.8/
rm -rf /packages/lambda_layer-python-3.7/
rm -rf /packages/lambda_layer-python-3.6/

echo "Zip files have been saved to docker volume /data. You can copy them locally like this:"
echo "docker run --rm -it -v \$(pwd):/packages <docker_image>"
echo "================================================================================"

