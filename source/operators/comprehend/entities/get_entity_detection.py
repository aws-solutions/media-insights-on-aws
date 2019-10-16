# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import tarfile
import os
from botocore import config
import json
from io import BytesIO
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
comprehend = boto3.client('comprehend', config=config)
s3_client = boto3.client('s3')
headers = {"Content-Type": "application/json"}


def read_from_s3(bucket, key):
    try:
        obj = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )
    except Exception as e:
        print("Exception occurred while reading asset metadata from s3")
        return {"Status": "Error", "Message": e}
    else:
        results = obj['Body'].read()
        return {"Status": "Success", "Object": results}


def lambda_handler(event, context):
    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        job_id = operator_object.metadata["comprehend_entity_job_id"]
        asset_id = operator_object.asset_id
        workflow_id = job_id
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(comprehend_error="No valid job id")
        raise MasExecutionError(operator_object.return_output_object())
    try:
        response = comprehend.list_entities_detection_jobs(
            Filter={
                'JobName': job_id,
            },
        )
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(comprehend_error="Unable to get response from comprehend: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        print(response)
        comprehend_status = response["EntitiesDetectionJobPropertiesList"][0]["JobStatus"]
        if comprehend_status == "SUBMITTED" or comprehend_status == "IN_PROGRESS":
            operator_object.add_workflow_metadata(comprehend_entity_job_id=job_id)
            operator_object.update_workflow_status("Executing")
            return operator_object.return_output_object()
        elif comprehend_status == "COMPLETED":
            output_uri = response["EntitiesDetectionJobPropertiesList"][0]["OutputDataConfig"]["S3Uri"]

            delimeter = '/'

            bucket = delimeter.join(output_uri.split(delimeter)[2:3])
            file_name = output_uri.split(delimeter)[-1]
            key = delimeter.join(output_uri.split(delimeter)[3:-1]) + '/' + file_name

            comprehend_tarball = read_from_s3(bucket, key)

            comprehend_data = {"LanguageCode": response['EntitiesDetectionJobPropertiesList'][0]['LanguageCode'], "Results": []}

            if comprehend_tarball["Status"] == "Success":
                input_bytes = comprehend_tarball["Object"]
                with tarfile.open(fileobj=BytesIO(input_bytes)) as tf:
                    for member in tf:
                        if member.isfile():
                            comprehend_data["Results"].append(tf.extractfile(member).read().decode('utf-8'))

                dataplane = DataPlane()

                metadata_upload = dataplane.store_asset_metadata(asset_id, "entities", workflow_id, comprehend_data)

                if "Status" not in metadata_upload:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(
                        comprehend_error="Unable to store entity data {e}".format(e=metadata_upload))
                    raise MasExecutionError(operator_object.return_output_object())
                else:
                    if metadata_upload["Status"] == "Success":
                        operator_object.update_workflow_status("Complete")
                        operator_object.add_workflow_metadata(comprehend_entity_job_id=job_id, output_uri=output_uri)
                        operator_object.update_workflow_status("Complete")
                        return operator_object.return_output_object()
                    else:
                        operator_object.update_workflow_status("Error")
                        operator_object.add_workflow_metadata(
                            comprehend_error="Unable to store entity data {e}".format(e=metadata_upload))
                        raise MasExecutionError(operator_object.return_output_object())
            else:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(comprehend_entity_job_id=job_id,
                                                  comprehend_error="could not retrieve output from s3: {e}".format(
                                                      e=comprehend_tarball["Message"]))
                raise MasExecutionError(operator_object.return_output_object())
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(comprehend_entity_job_id=job_id,
                                            comprehend_error="comprehend returned as failed: {e}".format(
                                                e=response["EntitiesDetectionJobPropertiesList"][0]["Message"]))
            raise MasExecutionError(operator_object.return_output_object())
