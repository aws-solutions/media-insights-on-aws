#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# PURPOSE:
# This function sends anonymized performance data to the AWS
# Solutions metrics API. This information is anonymized and helps improve the
# quality of the solution.

import uuid
import lib.cfnresponse as cfn
import lib.metrics as Metrics


def handler(event, context):
    print("We got this event:\n", event)
    # Each resource returns a promise with a json object to return cloudformation.
    try:
        request_type = event['RequestType']
        resource = event['ResourceProperties']['Resource']
        config = event['ResourceProperties']
        # Remove ServiceToken (lambda arn) to avoid sending AccountId
        config.pop("ServiceToken", None)
        config.pop("Resource", None)
        # Add some useful fields related to stack change
        config["CFTemplate"] = (
            request_type + "d"
        )  # Created, Updated, or Deleted
        response_data = {}
        print('Request::{} Resource::{}'.format(request_type, resource))
        if request_type == 'Create' or request_type == 'Update':
            if resource == 'UUID':
                response_data = {'UUID': str(uuid.uuid4())}
                unique_id = response_data['UUID']
                cfn.send(event, context, 'SUCCESS', response_data, unique_id)
            elif resource == 'AnonymizedMetric':
                Metrics.send_metrics(config)
                unique_id = 'Metrics Sent'
                cfn.send(event, context, 'SUCCESS', response_data, unique_id)
            else:
                print('Create failed, {} not defined in the Custom Resource'.format(resource))
                cfn.send(event, context, 'FAILED', {}, context.log_stream_name)
        elif request_type == 'Delete':
            print('RESPONSE:: {}: Not required to report data for delete request.'.format(resource))
            cfn.send(event, context, 'SUCCESS', {})
        else:
            print('RESPONSE:: {} Not supported'.format(request_type))
    except Exception as e:
        print('Exception: {}'.format(e))
        cfn.send(event, context, 'FAILED', {}, context.log_stream_name)
        print(e)
