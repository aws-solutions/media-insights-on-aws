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


var path = require("path");
var AWS = require('aws-sdk');
AWS.config.update({region: process.env.REGION});  
var s3 = new AWS.S3();

/**
 * Bootstraps videos to process into a clean account for testing
 */
exports.handler = async (event, context, callback) => {
  
    try
    {
        var inputBucket = 'mkt-anz';
        var inputVideos =
        [
            'aws-summit-on-demand-2018/Day1_1530_BuildingServerlessETLPipelineswithAmazonGlue_V2.appleuniversal.mp4',
            'aws-summit-on-demand-2018/Day2_1615_AdvancedContainerAutomationSecurityandMonitoring_V2.appleuniversal.mp4',
            '2018-02-19+12.00+Learn+How+to+Get+the+Right+Skills+to+Succeed+in+the+AWS+Cloud.mp4',
            'Build+Best+Practices+and+the+Right+Foundation+for+your+First+Production+Workload.mp4',
            'Optimising+Cost+%26+Efficiency+on+AWS+For+Newbies.mp4',
            'Build+Your+Case+for+the+Cloud_+How+to+Engage+Stakeholders+Across+Your+Business.mp4',
            '2017-05-25+11.00+AWS+Webinar_+Your+First+Step+to+Running+Applications+with+Containers.mp4',
            'AWS+Learning+Webinar+-+Cost+Optimisation+Best+Practices.mp4',
            'AWS+Learning+Webinar+-+An+Introduction+to+the+AWS+Well+Architected+Framework+(1).mp4',
            'Building+a+Modern+Data+Architecture+on+AWS+-+Learning+Webinar.mp4',
            'AWS+Webinar+Series+-+Build+web-based+and+native+mobile+applications+on+AWS.mp4',
            '2018-05-29+12.00+Supercharging+Applications+with+GraphQL+and+AWS+AppSync.mp4',
            '2018-02-15+12.00+Introduction+to+AWS+Cloud9.mp4',
            'AWS+reInvent+Recap+Webinar+2017.mp4'
        ];

        for (var i in inputVideos)
        {
            var inputVideoKey = inputVideos[i];
            var inputVideoFile = path.basename(inputVideoKey);

            var copyParams = { 
                CopySource: inputBucket + '/' + inputVideoKey,
                Bucket: process.env.OUTPUT_BUCKET,
                Key: 'videos/' + inputVideoFile
            };

            console.log('[INFO] copying: %s with parameters: %j', inputVideoFile, copyParams);
            await s3.copyObject(copyParams).promise();
            console.log('[INFO] successfully copied: %s', inputVideoFile);
        }
        
        callback(null, "Videos copied successfully");
    }
    catch (error)
    {
        console.log("Failed to copy videos", error);
        callback(error);
    }
};