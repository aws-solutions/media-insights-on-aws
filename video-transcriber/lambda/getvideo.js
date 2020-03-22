/**
  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License").
  You may not use this file except in compliance with the License.
  A copy of the License is located at

      http://www.apache.org/licenses/LICENSE-2.0

  or in the "license" file accompanying this file. This file is distributed
  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
  express or implied. See the License for the specific language governing
  permissions and limitations under the License.
*/

var AWS = require('aws-sdk');
AWS.config.update({region: process.env.REGION});  
var s3 = new AWS.S3();

/**
 * Gets a signed url to the video
 */
exports.handler = async (event, context, callback) => {

    console.log('[INFO] got event: %j', event);

    var responseHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true,
        'Content-Type': 'application/json'
    };

    try
    {
        var videoName = escape(event.pathParameters.videoName);

        const videoBucket = process.env.VIDEO_BUCKET;
        const signedUrlExpireSeconds = 60 * 60;

        const url = s3.getSignedUrl('getObject', {
            Bucket: videoBucket,
            Key: 'videos/' + videoName,
            Expires: signedUrlExpireSeconds
        });

        var video = {
            "s3VideoSignedUrl":  url
        };

        console.log('[INFO] made signed url: ' + url);

        const response = {
            statusCode: 200,
            headers: responseHeaders,
            body: JSON.stringify({  "video": video })
        };
        console.log('[INFO] response: %j', response);
        callback(null, response);
    }
    catch (error)
    {
        console.log("[ERROR] Failed to load video", error);
        const response = {
            statusCode: 500,
            headers: responseHeaders,
            body: JSON.stringify({  "message": "Failed to load video: " + error })
        };
        callback(null, response);
    }
};