###############################################################################
# PURPOSE:
#   Lambda function to detect body pose on a batch of video frames by Sagemaker inference.
#   It reads a list of frames from a json file - result of frame extraction Lambda -
#   and uses Pose inference pipeline model on Sagemaker to detect body pose in the frames.
#   WARNING: This function might needs longer Lambda timeouts depending on 
#   how many frames should be processed.
###############################################################################

import os
import json
import urllib
import boto3
import uuid
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

#Sagemaker inference pipeline endpoint must be deployed and provided as variable here
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
MIN_CONFIDENCE = os.environ['MIN_CONFIDENCE']
operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)

runtime= boto3.client('runtime.sagemaker')
s3 = boto3.client('s3')

def download_image(s3bucket, s3key):
    temp_img = '/tmp/temp_img'
    with open(temp_img, 'wb') as f:
        s3.download_fileobj(s3bucket, s3key, f)
    f.close()
    return temp_img

# Recognize pose in an image
def detect_pose(bucket, key, min_confidence):
    result = {}
    try:
        image = download_image(bucket, key)
        with open(image, 'rb') as f:
            payload = f.read()
        # Send image via InvokeEndpoint API
        output = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                        ContentType='application/x-image',
                                        Body=payload)
        result = json.loads(output['Body'].read().decode())
    except Exception as e:
        print("Error: " + str(e))
        #output_object.update_workflow_status("Error")
        #output_object.add_workflow_metadata(BatchPoseDetectionError=str(e))
        #raise MasExecutionError(output_object.return_output_object())
    
    #filtered = [ i for i in result['prediction'] if i[1]>=min_confidence]

    return result

# Lambda function entrypoint:
def lambda_handler(event, context):
    try:
        if "Images" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["Images"]["S3Bucket"]
            s3key = event["Input"]["Media"]["Images"]["S3Key"]
        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(BatchPoseDetectionError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())

    valid_image_types = [".json"]
    file_type = os.path.splitext(s3key)[1]
    
    # Image batch processing is synchronous.
    if file_type in valid_image_types:
        
        # Read metadata and list of frames
        chunk_details = json.loads(s3.get_object(Bucket=s3bucket, Key=s3key, )["Body"].read())
        
        chunk_result = []
        for img_s3key in chunk_details['s3_original_frames_keys']:
            # For each frame try to detect pose and save the results
            response = detect_pose(s3bucket, urllib.parse.unquote_plus(img_s3key), float(MIN_CONFIDENCE))
            if not response:
                continue
            frame_result = []
            segments  = response['pred_coords']
            confidence = response['confidence']
            frame_id, file_extension = os.path.splitext(os.path.basename(img_s3key))
            frame_result.append({'frame_id': frame_id[3:],
                                'Pose': {
                                    'points': segments[0],
                                    'confidence' : confidence[0]  
                                },
                                'Timestamp': chunk_details['timestamps'][frame_id]})
            if len(frame_result)>0: chunk_result+=frame_result
        
        response = {'metadata': chunk_details['metadata'],
                    'frames_result': chunk_result}

        output_object.update_workflow_status("Complete")
        output_object.add_workflow_metadata(AssetId=asset_id, WorkflowExecutionId=workflow_id)
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
        
        if metadata_upload["Status"] == "Success":
            print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
        elif metadata_upload["Status"] == "Failed":
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                BatchPoseDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        else:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                BatchPoseDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        return output_object.return_output_object()
    
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(BatchPoseDetectionError="Not a valid file type")
        raise MasExecutionError(output_object.return_output_object())