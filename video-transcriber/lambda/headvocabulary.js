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
var transcribe = new AWS.TranscribeService();

/**
 * Checks if vocabulary can currently be updated
 */
exports.handler = async (event, context, callback) => {

    console.log('[INFO] Event: %j', event);

    try
    {
		var statusCode;

        /**
         * Get vocabulary status
         */
        var vocabulary = await getVocabulary();

        console.log('[INFO] found vocabulary: %j', vocabulary);

        if (vocabulary.length > 0)
        {
            var status = vocabulary[0].VocabularyState;

            console.log('[INFO] found vocabulary status: ' + status);

            if (status == 'PENDING')
            {
                console.log('[INFO] vocabulary cannot be updated now');
                statusCode = 204;
            }
            else if (status == 'FAILED')
            {
            	console.log('[INFO] vocabulary failed to update');
                statusCode = 202;
            }
            else
            {
                console.log('[INFO] vocabulary can be updated now');
                statusCode = 200;
            }
        }
        else
        {
            console.log('[INFO] no existing vocabulary, vocabulary can be updated now');
            statusCode = 200;
        }

	    var responseHeaders = {
	        'Access-Control-Allow-Origin': '*',
	        'Access-Control-Allow-Credentials': true
	    }; 
	    
        const response = {
            statusCode: statusCode,
            headers: responseHeaders
        };

        callback(null, response);
    }
    catch (error)
    {
        console.log("Failed to check vocabulary ready status", error);
        const response = {
            statusCode: 500,
            headers: responseHeaders,
            body: JSON.stringify({ "message": "Failed to check vocabulary ready status: " + error })
        };
        callback(null, response);
    }

};

/**
 * Fetch custom vocabulary from transcribe
 */
async function getVocabulary()
{
    try
    {
        var vocabulary = [];

        var vocabularyName = process.env.VOCABULARY_NAME;

        var getVocabularyParams = {
            VocabularyName: vocabularyName
        };

        console.log('[INFO] getting vocabulary using params: %j', getVocabularyParams);

        var getVocabularyResponse = await transcribe.getVocabulary(getVocabularyParams).promise();

        console.log('[INFO] got get vocabulary response: %j', getVocabularyResponse);

        if (getVocabularyResponse)
        {
            vocabulary.push(getVocabularyResponse);
        }

        return vocabulary;
    }
    catch (error)
    {
        console.log('[ERROR] failed to get vocabulary');
        throw error;
    }
}
