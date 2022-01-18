#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License Version 2.0 (the "License").            #
#  You may not use this file except in compliance with the License.          #
#  A copy of the License is located at                                       #
#                                                                            #
#      http://www.apache.org/licenses/                                       #
#                                                                            #
#  or in the "license" file accompanying this file. This file is distributed #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,        #
#  express or implied. See the License for the specific language governing   #
#  permissions and limitations under the License.                            #
##############################################################################
#
# PURPOSE:
# This function sends anonymous performance data to the AWS
# Solutions metrics API. This information is anonymous and helps improve the
# quality of the solution.
#
##############################################################################

import uuid
import lib.cfnresponse as cfn
import lib.metrics as Metrics

def handler(event, context):
    print("We got this event:\n", event)
    # Each resource returns a promise with a json object to return cloudformation.
    try:
        requestType = event['RequestType']
        resource = event['ResourceProperties']['Resource']
        config = event['ResourceProperties']
        # Remove ServiceToken (lambda arn) to avoid sending AccountId
        config.pop("ServiceToken", None)
        config.pop("Resource", None)
        # Add some useful fields related to stack change
        config["CFTemplate"] = (
                requestType + "d"
        )  # Created, Updated, or Deleted
        responseData = {}
        print('Request::{} Resource::{}'.format(requestType, resource))
        if requestType == 'Create' or requestType == 'Update':
            if resource == 'UUID':
                responseData = {'UUID':str(uuid.uuid4())}
                id = responseData['UUID']
                cfn.send(event, context, 'SUCCESS', responseData, id)
            elif resource == 'AnonymousMetric':
                Metrics.send_metrics(config)
                id = 'Metrics Sent'
                cfn.send(event, context, 'SUCCESS', responseData, id)
            else:
                print('Create failed, {} not defined in the Custom Resource'.format(resource))
                cfn.send(event, context, 'FAILED', {}, context.log_stream_name)
        elif requestType == 'Delete':
            print('RESPONSE:: {}: Not required to report data for delete request.'.format(resource))
            cfn.send(event, context, 'SUCCESS', {})
        else:
            print('RESPONSE:: {} Not supported'.format(requestType))
    except Exception as e:
        print('Exception: {}'.format(e))
        cfn.send(event, context, 'FAILED', {}, context.log_stream_name)
        print(e)
