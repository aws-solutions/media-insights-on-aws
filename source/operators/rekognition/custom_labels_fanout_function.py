import os
import json
import urllib
import boto3
import uuid
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

s3 = boto3.client('s3')

# Minimum Rekognition Detect Custom Label Treshold
MIN_CONFIDENCE = 10

# Recognizes custom labels in an image
def detect_custom_labels(projectVersionArn,bucket, key):
    rek = boto3.client('rekognition')
    try:
        print("**********")
        print(bucket)
        print(key)
        print(projectVersionArn)
        response = rek.detect_custom_labels(ProjectVersionArn=projectVersionArn ,Image={'S3Object': {'Bucket': bucket, 'Name': key}})
        print(response)
        #response = rek.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': key}})
    except Exception as e:
        #output_object.update_workflow_status("Error")
        #output_object.add_workflow_metadata(CustomLabelDetectionError=str(e))
        raise MasExecutionError(e)
    return response
    
    
def lambda_handler(event, context):
    try:
        #{'asset_id': asset_id,'operator_name': operator_name,'workflow_id': workflow_id,'projectVersionArn':projectVersionArn, 'bucket': s3bucket, 'img_s3key': img_s3key, 'end': end}
        print("event is " + str(event))
        chunk_details = event["chunk_details"]
        workflow_id = event["workflow_id"]
        asset_id = event['asset_id']
        operator_name = event['operator_name']
        projectVersionArn = event['projectVersionArn']
        s3bucket = event['bucket']
        img_s3key = event['img_s3key']
        end = event['end']
        print("image key is " + img_s3key)
        print("is end is " + str(end))
        response = detect_custom_labels(projectVersionArn,s3bucket, urllib.parse.unquote_plus(img_s3key))
        chunk_result = []
        frame_result = []
        for i in response['CustomLabels']:
            if i['Confidence'] > MIN_CONFIDENCE:
                bbox = i['Geometry']['BoundingBox']
                frame_id, file_extension = os.path.splitext(os.path.basename(img_s3key))
                frame_result.append({'frame_id': frame_id[3:],
                            'Text': {
                                'BoundingBox': bbox
                            },
                            'Confidence': i['Confidence'],
                            'Name': i['Name'],
                            'Timestamp': chunk_details['timestamps'][frame_id]})
                print("frame result is " + str(frame_result))
        if len(frame_result)>0: chunk_result=frame_result
        print("chunk result is " + str(chunk_result))
        response = {'metadata': chunk_details['metadata'],
                'frames_result': chunk_result}
        print("response is " + str(response))
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response,paginate=True,end=end)
            
        if metadata_upload["Status"] == "Success":
            print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
        elif metadata_upload["Status"] == "Failed":
            raise MasExecutionError("failed to upload metadata")
        else:
            raise MasExecutionError("failed to upload metadata")
            return
    
    except Exception as e:
        raise MasExecutionError(e)
