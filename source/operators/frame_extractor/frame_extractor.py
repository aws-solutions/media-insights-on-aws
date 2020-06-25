###############################################################################
# PURPOSE:
#   Lambda function to extract frames from video files using cv2 and store on S3.
#   WARNING: This function might needs longer Lambda timeouts depending on chunk 
#   size and how many frames should be extracted.
###############################################################################

import cv2
import base64
import json
import os
import boto3
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

# Environment Variables
store_frames=os.environ.get("STORE_FRAMES", "None")
frame_resize_width=int(os.environ.get("FRAME_RESIZE_WIDTH", 480 ))
frame_resize_height=int(os.environ.get("FRAME_RESIZE_HEIGHT", 320 ))
FPSE = 2 #setting to 2 frames per second to improve throughput of downstream processing

s3 = boto3.client('s3')

def download_chunk(s3bucket, s3key):
    temp_chunk = '/tmp/temp_chunk'
    with open(temp_chunk, 'wb') as f:
        s3.download_fileobj(s3bucket, s3key, f)
    f.close()
    return temp_chunk

def put_record_s3(s3bucket, asset_id, chunk_id, frames):
    file_name = 'private/assets/{}/output/{}/frame_list.json'.format(asset_id, chunk_id)
    try:
        s3.put_object( 
            ACL='bucket-owner-full-control', 
            Bucket=s3bucket, 
            Key=file_name, 
            Body=json.dumps({"chunk": frames}).encode()
        )
    except Exception as e:
        print("put_record_s3: Failed saving file %s" % file_name)
        print (e)

def lambda_handler(event, context):
    print("We got the following event:\n", event)
    output_object = MediaInsightsOperationHelper(event)

    if store_frames not in ["all", "original", "resized"]:
        return "Invalid STORE_FRAMES option: %s (Valid: all, original, resized)" % store_frames

    store_original_frames = store_frames in ["all", "original"]
    store_resized_frames = store_frames in ["all", "resized" ]

    try:
        if "Video" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["Video"]["S3Bucket"]
            s3key = event["Input"]["Media"]["Video"]["S3Key"]
        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(FrameExtractionError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())
    print("Processing s3://"+s3bucket+"/"+s3key)
    valid_video_types = [".avi", ".mp4", ".mov", ".ts"]
    file_type = os.path.splitext(s3key)[1]

    print("Event:\n", event)
    
    if file_type in valid_video_types:
        # Extract frames and store paths in a list to persist on the dataplane
        file_name = download_chunk(s3bucket, s3key)

        cap = cv2.VideoCapture(file_name)
        
        metadata = {
            'original_frame_width': cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            'original_frame_height': cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            'frame_width': frame_resize_width,
            'frame_height': frame_resize_height,
            'fourcc': cap.get(cv2.CAP_PROP_FOURCC),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'format': cap.get(cv2.CAP_PROP_FORMAT),
            'mode': cap.get(cv2.CAP_PROP_MODE),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'workflow_id': workflow_id,
            'asset_id': asset_id,
            'store_frames': store_frames
        }
        
        # Lists to capture timestamps
        timestamp = []
        store_timestamps = {}
        
        original_frame_keys = []
        resized_frame_keys = []
        frame_counter = 0
        chunk_id = os.path.basename(s3key).split('.')[0]
        
        hop = round (metadata['fps']/FPSE)
        if hop == 0: hop = 1 # if FPSE is invalid extract every frame 
        print('hop is ')
        print(hop)
        while(cap.isOpened()):
            _, frame = cap.read()

            if _ == False:
                break
            if frame_counter % hop == 0:
                if store_original_frames:
                    jpg = cv2.imencode(".jpg", frame)[1]
                    frame_key = 'private/assets/%s/output/%s/original/id_%d.jpg' % (asset_id, chunk_id, frame_counter)
                    s3.put_object( ACL='bucket-owner-full-control', Bucket=s3bucket, Key=frame_key, Body=bytearray(jpg))
                    original_frame_keys.append(frame_key)
                    frame_id = 'id_%d' % (frame_counter)
                    timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC))
                    store_timestamps[frame_id] = timestamp
    
                if store_resized_frames:
                    frame = cv2.resize(frame, (frame_resize_width, frame_resize_height))
                    jpg = cv2.imencode(".jpg", frame)[1]
                    frame_key = 'private/assets/%s/output/%s/resized/id_%d.jpg' % (asset_id, chunk_id, frame_counter)
                    s3.put_object( ACL='bucket-owner-full-control', Bucket=s3bucket, Key=frame_key, Body=bytearray(jpg))
                    resized_frame_keys.append(frame_key)
                    frame_id = 'id_%d' % (frame_counter)
                    timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC))
                    store_timestamps[frame_id] = timestamp

            frame_counter += 1
        
        if metadata['frame_count'] != frame_counter:
            print("Can't read all frames: expected[%d] read[%d]" % (metadata['frame_count'], frame_counter))
            metadata['frame_count'] = frame_counter
        
        response = {
            'metadata': metadata,
            's3_original_frames_keys': original_frame_keys,
            's3_resized_frame_keys': resized_frame_keys,
            'timestamps': store_timestamps
        }
        
        put_record_s3(s3bucket, asset_id, chunk_id, response)
        
        output_object.update_workflow_status("Complete")
        output_object.add_workflow_metadata(AssetId=asset_id, WorkflowExecutionId=workflow_id)

        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, 'frameExtractor', workflow_id, response)
        
        if metadata_upload["Status"] == "Success":
            print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
            # add frame list to output
            output_object.add_media_object('Images', metadata_upload['Bucket'], metadata_upload['Key'])
        elif metadata_upload["Status"] == "Failed":
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                FrameExtractionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        else:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                FrameExtractionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        
        return output_object.return_output_object()
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(FrameExtractionError="Not a valid file type")
        raise MasExecutionError(output_object.return_output_object())