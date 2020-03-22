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
 * Updates vocabulary in AWS Transcribe,
 * creates the vocabulary if it does not exist
 */
exports.handler = async (event, context, callback) => {

    console.log("Event: %j", event);

    var responseHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true,
        'Content-Type': 'application/json'
    };

    try
    {
        var vocabularyName = process.env.VOCABULARY_NAME;
        var transcribeLanguage = process.env.TRANSCRIBE_LANGUAGE;

        /**
         * The vocabulary submitted by the user
         */
        var vocabulary = JSON.parse(event.body);

        /**
         * Check to see if the vocabulary exists
         */
        var vocabularies = await getVocabulary();

        if (vocabularies.length > 0)
        {
            console.log('[INFO] existing vocabulary found: %j', vocabularies[0]);

            /**
             * Update the vocabulary
             */
            var updateVocabularyParams = {
                LanguageCode: transcribeLanguage,
                VocabularyName: vocabularyName,
                Phrases: vocabulary.vocabulary
            };

            var updateVocabularyResponse = await transcribe.updateVocabulary(updateVocabularyParams).promise();

            console.log('[INFO] got update vocabulary response: %j', updateVocabularyResponse);            
        }
        else {
            throw new Error('No existing vocabulary found');
        }

        vocabulary.canUpdate = false;

        const response = {
            statusCode: 200,
            headers: responseHeaders,
            body: JSON.stringify(vocabulary)
        };

        callback(null, response);
    }
    catch (error)
    {
        console.log("Failed to update vocabulary", error);

        const response = {
            statusCode: 500,
            headers: responseHeaders,
            body: JSON.stringify({ "message": "Failed to update vocabulary: " + error })
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
