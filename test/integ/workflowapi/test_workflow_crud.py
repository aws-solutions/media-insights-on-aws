# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MIE workflow API
#
# PRECONDITIONS:
# MIE base stack must be deployed in your AWS account
#
# Boto3 will raise a deprecation warning (known issue). It's safe to ignore.
#
# USAGE:
#   cd tests/
#   pytest -s -W ignore::DeprecationWarning -p no:cacheprovider
#
###############################################################################

import urllib3
import time

# local imports
import validation


def test_workflow_api(workflow_api, api_schema, operation_configs, stage_configs, workflow_configs):
    api = workflow_api()
    schema = api_schema
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Running /workflow/operation API create tests")

    for operation_config in operation_configs:
        print ("\n----------------------------------------")
        print("\nTEST CONFIGURATION: {}".format(operation_config))
        start_lambda = operation_config["Input"] + operation_config["Type"] + operation_config["Status"] + "Lambda"

        # Create the operation

        operation_body = {
            "StartLambdaArn": api.stack_resources[start_lambda],
            "Configuration": {
                "MediaType": operation_config["Input"],
                "Enabled": True
            },
            "Type": operation_config["Type"],
            "Name": operation_config["Name"]
        }

        if (operation_config["Type"] == "Async"):
            monitor_lambda = operation_config["Input"]+operation_config["Type"]+operation_config["Status"]+"MonitorLambda"
            operation_body["MonitorLambdaArn"] = api.stack_resources[monitor_lambda]

        if "OutputMediaType" in operation_config:
            operation_body["Configuration"]["OutputMediaType"] = operation_config["OutputMediaType"]

        if "TestCustomConfig" in operation_config:
            operation_body["Configuration"]["TestCustomConfig"] = operation_config["TestCustomConfig"]

        create_operation_response = api.create_operation_request(operation_body)
        assert create_operation_response.status_code == 200
        validation.schema(create_operation_response.json(), api_schema["create_operation_response"])

        # Read the operation

        print("Running /workflow/operation API read tests")

        get_operation_response = api.get_operation_request(operation_config["Name"])
        assert get_operation_response.status_code == 200

    print("Running /workflow/stage API create tests")

    for stage_config in stage_configs:
        print("\n----------------------------------------")
        print("\nTEST CONFIGURATION: {}".format(stage_config))

        # Create the stage

        stage_body = {
            "Name": stage_config["Name"],
            "Operations": stage_config["Operations"]
        }

        create_stage_response = api.create_stage_request(stage_body)
        assert create_stage_response.status_code == 200
        validation.schema(create_stage_response.json(), api_schema["create_stage_response"])

        # Read the stage

        print("Running /workflow/stage API read tests")

        get_stage_response = api.get_stage_request(stage_config["Name"])
        assert get_stage_response.status_code == 200

    print("Running /workflow API create tests")

    for workflow_config in workflow_configs:
        print("\n----------------------------------------")
        print("\nTEST CONFIGURATION: {}".format(workflow_config))

        workflow_body = {
            "Name":workflow_config["Name"],
            "StartAt": stage_configs[0]["Name"]
        }

        workflow_stages = {}
        num_stages = len(stage_configs)
        i = 1
        for stages in stage_configs:
            if i == num_stages:
                workflow_stages[stages["Name"]] = {
                    "End": True
                }
            else:
                workflow_stages[stages["Name"]] = {
                    "Next": stage_configs[i]["Name"]
                }
            i = i + 1

        workflow_body["Stages"] = workflow_stages

        create_workflow_response = api.create_workflow_request(workflow_body)
        assert create_workflow_response.status_code == 200
        # FIXME - need to update schema manually
        # #validation.schema(workflow, api_schema["create_workflow_response"])

    print("Running /workflow API delete tests")

    # Delete the workflow
    time.sleep(10)
    for workflow_config in workflow_configs:
        delete_workflow_response = api.delete_workflow_request(workflow_config["Name"])
        print(delete_workflow_response.json())
        assert delete_workflow_response.status_code == 200

    print("Running /workflow/stage API delete tests")

    # Delete the stages
    for stage_config in stage_configs:
        delete_stage_response = api.delete_stage_request(stage_config["Name"])
        assert delete_stage_response.status_code == 200

    print("Running /workflow/operation API delete tests")

    # Delete the operations
    for operation_config in operation_configs:
        delete_workflow_response = api.delete_operation_request(operation_config["Name"])
        assert delete_workflow_response.status_code == 200
