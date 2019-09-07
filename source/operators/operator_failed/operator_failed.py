# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import ast
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper


def lambda_handler(event, context):

    print("Received: ", event)

    formatted_output = {}

    # Check if the failure came from a catch state by seeing if the Outputs key exists

    try:
        error = event["Outputs"]
    except KeyError:

        # If Outputs key does not exist, then we got here from the 'Did Complete' choice
        # This means we can just return the event as is to the control plane
        print("Returning the following event to the controlplane: ", event)
        return event
    else:
        try:
            # Pull in required keys from top level event object
            formatted_output["Name"] = event["Name"]
            formatted_output["AssetId"] = event["AssetId"]
            formatted_output["WorkflowExecutionId"] = event["WorkflowExecutionId"]
            formatted_output["Input"] = event["Input"]
            formatted_output["Configuration"] = event["Configuration"]

        except KeyError as e:
            print("Missing a required key for building the output object: ", e)
            raise Exception
        else:
            # Check to see where the exception came from

            if error["Error"] is not "MasExecutionError":
                formatted_output["MetaData"] = {}
                formatted_output["MetaData"]["{name}Error".format(name=event["Name"])] = error["Error"]

            else:
                # Pull in metadata keys from outputs

                # Unfortunately step functions stores this information in a doubly nested single quotes string within json
                failed_state_info = json.loads(json.dumps(ast.literal_eval(json.loads(error["Cause"])["errorMessage"])))

                formatted_output["MetaData"] = failed_state_info["MetaData"]

            # Set status to error
            formatted_output["Status"] = "Error"

            output_object = MediaInsightsOperationHelper(formatted_output)

            print("Returning the following event to the controlplane: ", output_object.return_output_object())
            return output_object.return_output_object()

