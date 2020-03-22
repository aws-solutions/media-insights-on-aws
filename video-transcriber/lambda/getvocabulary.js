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
const fetch = require('node-fetch');

/**
 * Loads custom vocabulary from AWS Transcribe
 */
exports.handler = async (event, context, callback) => {

    try
    {
        var responseHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': true,
            'Content-Type': 'application/json'
        };

        var vocabParams = {
            VocabularyName: process.env.VOCABULARY_NAME
        };

        var transcribeResponse = await transcribe.getVocabulary(vocabParams).promise();

        const get = await fetch(transcribeResponse.DownloadUri, {method: 'GET'});
        const vocabularyText = await get.text();

        var vocabulary = vocabularyText.split('\n').filter(function(e) {
            return e !== "ENDOFDICTIONARYTRANSCRIBE";
        });

        const response = {
            statusCode: 200,
            headers: responseHeaders,
            body: JSON.stringify({ "vocabulary": vocabulary })
        };

        callback(null, response);
    }
    catch (error)
    {
        console.log("Failed to fetch vocabulary", error);
        console.log("Vocabulary does not exist");
        const response = {
            statusCode: 200,
            headers: responseHeaders,
            body: JSON.stringify({ "vocabulary": [ ] })
        };
        callback(null, response);
    }
    
};