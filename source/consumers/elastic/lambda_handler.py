# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from elasticsearch import Elasticsearch, RequestsHttpConnection
import base64
import json
import os
import boto3
from requests_aws4auth import AWS4Auth

es_endpoint = os.environ['EsEndpoint']
dataplane_bucket = os.environ['DataplaneBucket']

s3 = boto3.client('s3')

# These names are the lowercase version of OPERATOR_NAME defined in /source/operators/operator-library.yaml
supported_operators = ["textdetection", "mediainfo", "transcribe", "translate", "genericdatalookup", "labeldetection", "celebrityrecognition", "facesearch", "contentmoderation", "facedetection", "key_phrases", "entities", "key_phrases"]


def normalize_confidence(confidence_value):
    converted = float(confidence_value) * 100
    return str(converted)


def convert_to_milliseconds(time_value):
    converted = float(time_value) * 1000
    return str(converted)

def process_text_detection(asset, workflow, results):
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    # We can tell if json results are paged by checking to see if the json results are an instance of the list type.
    if isinstance(metadata, list):
        # handle paged results
        for page in metadata:
            if len(page["TextDetections"]) > 0:
                for item in page["TextDetections"]:
                    try:
                        text_detection = item["TextDetection"]
                        text_detection["Timestamp"] = item["Timestamp"]
                        text_detection["Operator"] = "textDetection"
                        text_detection["Workflow"] = workflow
                        # Flatten the bbox Label array
                        text_detection["BoundingBox"] = text_detection["Geometry"]["BoundingBox"]
                        del text_detection["Geometry"]
                        print(text_detection)
                        extracted_items.append(text_detection)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    else:
        # these results are not paged
        if len(metadata["TextDetections"]) > 0:
                for item in metadata["TextDetections"]:
                    try:
                        text_detection = item["TextDetection"]
                        text_detection["Timestamp"] = item["Timestamp"]
                        text_detection["Operator"] = "textDetection"
                        text_detection["Workflow"] = workflow
                        # Flatten the bbox Label array
                        text_detection["BoundingBox"] = text_detection["Geometry"]["BoundingBox"]
                        del text_detection["Geometry"]
                        extracted_items.append(text_detection)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    bulk_index(es, asset, "textDetection", extracted_items)


def process_celebrity_detection(asset, workflow, results):
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    if isinstance(metadata, list):
        for page in metadata:
            # Parse schema for videos:
            # https://docs.aws.amazon.com/rekognition/latest/dg/celebrities-video-sqs.html
            if "Celebrities" in page:
                for item in page["Celebrities"]:
                    try:
                        item["Operator"] = "celebrity_detection"
                        item["Workflow"] = workflow
                        if "Celebrity" in item:
                            # flatten the inner Celebrity array
                            item["Name"] = item["Celebrity"]["Name"]
                            item["Confidence"] = item["Celebrity"]["Confidence"]
                            # Bounding box can be around body or face. Prefer body.
                            bounding_box = ''
                            if 'BoundingBox' in item["Celebrity"]:
                                bounding_box = item["Celebrity"]["BoundingBox"]
                            elif 'BoundingBox' in item["Celebrity"]["Face"]:
                                bounding_box = item["Celebrity"]["Face"]["BoundingBox"]
                            item["BoundingBox"] = bounding_box
                            # Set IMDB URL if it exists.
                            url=''
                            if item["Celebrity"]["Urls"]:
                                url = item["Celebrity"]["Urls"][0]
                            item['URL'] = url
                            # delete flattened array
                            del item["Celebrity"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
            # Parse schema for images:
            # https://docs.aws.amazon.com/rekognition/latest/dg/API_RecognizeCelebrities.html
            if "CelebrityFaces" in page:
                for item in page["CelebrityFaces"]:
                    try:
                        item["Operator"] = "celebrity_detection"
                        item["Workflow"] = workflow
                        if "Face" in item:
                            # flatten the inner Face array
                            item["Confidence"] = item["Face"]["Confidence"]
                            item["BoundingBox"] = item["Face"]["BoundingBox"]
                            # delete flattened array
                            del item["Face"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    else:
        # Parse schema for videos:
        if "Celebrities" in metadata:
            for item in metadata["Celebrities"]:
                try:
                    item["Operator"] = "celebrity_detection"
                    item["Workflow"] = workflow
                    if "Celebrity" in item:
                        # flatten the inner Celebrity array
                        item["Name"] = item["Celebrity"]["Name"]
                        item["Confidence"] = item["Celebrity"]["Confidence"]
                        # Bounding box can be around body or face. Prefer body.
                        item["BoundingBox"] = ''
                        if 'BoundingBox' in item["Celebrity"]:
                            item["BoundingBox"] = item["Celebrity"]["BoundingBox"]
                        elif 'BoundingBox' in item["Celebrity"]["Face"]:
                            item["BoundingBox"] = item["Celebrity"]["Face"]["BoundingBox"]
                        # Set IMDB URL if it exists.
                        url=''
                        if item["Celebrity"]["Urls"]:
                            url = item["Celebrity"]["Urls"][0]
                        item['URL'] = url
                        # delete flattened array
                        del item["Celebrity"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
        # Parse schema for images:
        if "CelebrityFaces" in metadata:
            for item in metadata["CelebrityFaces"]:
                try:
                    item["Operator"] = "celebrity_detection"
                    item["Workflow"] = workflow
                    if "Face" in item:
                        # flatten the inner Face array
                        item["Confidence"] = item["Face"]["Confidence"]
                        item["BoundingBox"] = item["Face"]["BoundingBox"]
                        # delete flattened array
                        del item["Face"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
    bulk_index(es, asset, "celebrity_detection", extracted_items)


def process_content_moderation(asset, workflow, results):
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    if isinstance(metadata, list):
        for page in metadata:
            if "ModerationLabels" in page:
                for item in page["ModerationLabels"]:
                    try:
                        item["Operator"] = "content_moderation"
                        item["Workflow"] = workflow
                        if "ModerationLabel" in item:
                            # flatten the inner ModerationLabel array
                            item["Name"] = item["ModerationLabel"]["Name"]
                            item["ParentName"] = ''
                            if 'ParentName' in item["ModerationLabel"]:
                                item["ParentName"] = item["ModerationLabel"]["ParentName"]
                            item["Confidence"] = ''
                            if 'Confidence' in item["ModerationLabel"]:
                                item["Confidence"] = item["ModerationLabel"]["Confidence"]
                            # Delete the flattened array
                            del item["ModerationLabel"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    else:
        if "ModerationLabels" in metadata:
            for item in metadata["ModerationLabels"]:
                try:
                    item["Operator"] = "content_moderation"
                    item["Workflow"] = workflow
                    if "ModerationLabel" in item:
                        # flatten the inner ModerationLabel array
                        item["Name"] = item["ModerationLabel"]["Name"]
                        item["ParentName"] = ''
                        if 'ParentName' in item["ModerationLabel"]:
                            item["ParentName"] = item["ModerationLabel"]["ParentName"]
                        item["Confidence"] = ''
                        if 'Confidence' in item["ModerationLabel"]:
                            item["Confidence"] = item["ModerationLabel"]["Confidence"]
                        # Delete the flattened array
                        del item["ModerationLabel"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
    bulk_index(es, asset, "content_moderation", extracted_items)


def process_face_search(asset, workflow, results):
    metadata = json.loads(results)
    es = connect_es(es_endpoint)

    extracted_items = []
    if isinstance(metadata, list):
        for page in metadata:
            if "Persons" in page:
                for item in page["Persons"]:
                    item["Operator"] = "faceSearch"
                    item["Workflow"] = workflow
                    # flatten person key
                    item["PersonIndex"] = item["Person"]["Index"]
                    if "BoundingBox" in item["Person"]:
                        item["PersonBoundingBox"] = item["Person"]["BoundingBox"]
                    # flatten face key
                    if "Face" in item["Person"]:
                        item["FaceBoundingBox"] = item["Person"]["Face"]["BoundingBox"]
                        item["FaceLandmarks"] = item["Person"]["Face"]["Landmarks"]
                        item["FacePose"] = item["Person"]["Face"]["Pose"]
                        item["FaceQuality"] = item["Person"]["Face"]["Quality"]
                        confidence = item["Person"]["Face"]["Confidence"]
                        item["Confidence"] = confidence

                    if "FaceMatches" in item:
                        item["ContainsKnownFace"] = True
                        # flatten face matches key
                        for face in item["FaceMatches"]:
                            item["KnownFaceSimilarity"] = face["Similarity"]
                            item["MatchingKnownFaceId"] = face["Face"]["FaceId"]
                            item["ExternalImageId"] = face["Face"]["ExternalImageId"]
                            item["KnownFaceBoundingBox"] = face["Face"]["BoundingBox"]
                            item["ImageId"] = face["Face"]["ImageId"]
                        del item["FaceMatches"]
                    else:
                        item["ContainsKnownFace"] = False
                    del item["Person"]

                    extracted_items.append(item)

    else:
        if "Persons" in metadata:
            for item in metadata["Persons"]:
                item["Operator"] = "faceSearch"
                item["Workflow"] = workflow
                # flatten person key
                item["PersonIndex"] = item["Person"]["Index"]
                if "BoundingBox" in item["Person"]:
                    item["PersonBoundingBox"] = item["Person"]["BoundingBox"]
                #flatten face key
                if "Face" in item["Person"]:
                    item["FaceBoundingBox"] = item["Person"]["Face"]["BoundingBox"]
                    item["FaceLandmarks"] = item["Person"]["Face"]["Landmarks"]
                    item["FacePose"] = item["Person"]["Face"]["Pose"]
                    item["FaceQuality"] = item["Person"]["Face"]["Quality"]
                    confidence = item["Person"]["Face"]["Confidence"]
                    item["Confidence"] = confidence

                if "FaceMatches" in item:
                    item["ContainsKnownFace"] = True
                    # flatten face matches key
                    for face in item["FaceMatches"]:
                        item["KnownFaceSimilarity"] = face["Similarity"]
                        item["MatchingKnownFaceId"] = face["Face"]["FaceId"]
                        item["KnownFaceBoundingBox"] = face["Face"]["BoundingBox"]
                        item["ImageId"] = face["Face"]["ImageId"]
                    del item["FaceMatches"]
                else:
                    item["ContainsKnownFace"] = False
                del item["Person"]

                extracted_items.append(item)

    bulk_index(es, asset, "face_search", extracted_items)


def process_face_detection(asset, workflow, results):
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    if isinstance(metadata, list):
        for page in metadata:
            # Parse schema for video:
            if "Faces" in page:
                for item in page["Faces"]:
                    try:
                        item["Operator"] = "face_detection"
                        item["Workflow"] = workflow
                        if "Face" in item:
                            # flatten the inner Face array
                            item["BoundingBox"] = item["Face"]["BoundingBox"]
                            item["AgeRange"] = item["Face"]["AgeRange"]
                            item["Smile"] = item["Face"]["Smile"]
                            item["Eyeglasses"] = item["Face"]["Eyeglasses"]
                            item["Sunglasses"] = item["Face"]["Sunglasses"]
                            item["Gender"] = item["Face"]["Gender"]
                            item["Beard"] = item["Face"]["Beard"]
                            item["Mustache"] = item["Face"]["Mustache"]
                            item["EyesOpen"] = item["Face"]["EyesOpen"]
                            item["MouthOpen"] = item["Face"]["MouthOpen"]
                            item["Emotions"] = item["Face"]["Emotions"]
                            item["Confidence"] = item["Face"]["Confidence"]
                            # Delete the flattened array
                            del item["Face"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
            # Parse schema for images:
            if "FaceDetails" in page:
                for item in page["FaceDetails"]:
                    item["Operator"] = "face_detection"
                    item["Workflow"] = workflow
                    extracted_items.append(item)
    else:
        # Parse schema for videos:
        if "Faces" in metadata:
            for item in metadata["Faces"]:
                try:
                    item["Operator"] = "face_detection"
                    item["Workflow"] = workflow
                    if "Face" in item:
                        # flatten the inner Face array
                        item["BoundingBox"] = item["Face"]["BoundingBox"]
                        item["AgeRange"] = item["Face"]["AgeRange"]
                        item["Smile"] = item["Face"]["Smile"]
                        item["Eyeglasses"] = item["Face"]["Eyeglasses"]
                        item["Sunglasses"] = item["Face"]["Sunglasses"]
                        item["Gender"] = item["Face"]["Gender"]
                        item["Beard"] = item["Face"]["Beard"]
                        item["Mustache"] = item["Face"]["Mustache"]
                        item["EyesOpen"] = item["Face"]["EyesOpen"]
                        item["MouthOpen"] = item["Face"]["MouthOpen"]
                        item["Emotions"] = item["Face"]["Emotions"]
                        item["Confidence"] = item["Face"]["Confidence"]
                        # Delete the flattened array
                        del item["Face"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
        # Parse schema for images:
        if "FaceDetails" in metadata:
            for item in metadata["FaceDetails"]:
                item["Operator"] = "face_detection"
                item["Workflow"] = workflow
                extracted_items.append(item)
    bulk_index(es, asset, "face_detection", extracted_items)

def process_mediainfo(asset, workflow, results):
    # This function puts mediainfo data in Elasticsearch.
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    # Objects in arrays are not well supported by Elastic, so we flatten the tracks array here.
    if isinstance(metadata['tracks'], list):
        for item in metadata['tracks']:
            item["Operator"] = "mediainfo"
            item["Workflow"] = workflow
            extracted_items.append(item)
    bulk_index(es, asset, "mediainfo", extracted_items)

def process_generic_data(asset, workflow, results):
    # This function puts generic data in Elasticsearch.
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    # We can tell if json results are paged by checking to see if the json results are an instance of the list type.
    if isinstance(metadata, list):
        # handle paged results
        for page in metadata:
            if "Labels" in page:
                for item in page["Labels"]:
                    try:
                        item["Operator"] = "generic_data_lookup"
                        item["Workflow"] = workflow
                        if "Label" in item:
                            # Flatten the inner Label array
                            item["Confidence"] = float(item["Label"]["Confidence"])*100
                            item["Name"] = item["Label"]["Name"]
                            item["Instances"] = ''
                            if 'Instances' in item["Label"]:
                                for box in item["Label"]["Instances"]:
                                    box["BoundingBox"]["Height"] = float(box["BoundingBox"]["Height"]) / 720
                                    box["BoundingBox"]["Top"] = float(box["BoundingBox"]["Top"]) / 720
                                    box["BoundingBox"]["Left"] = float(box["BoundingBox"]["Left"]) / 1280
                                    box["BoundingBox"]["Width"] = float(box["BoundingBox"]["Width"]) / 1280
                                    box["Confidence"] = float(box["Confidence"])*100
                                item["Instances"] = item["Label"]["Instances"]
                            item["Parents"] = ''
                            if 'Parents' in item["Label"]:
                                item["Parents"] = item["Label"]["Parents"]
                            # Delete the flattened array
                            del item["Label"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    else:
        # these results are not paged
        if "Labels" in metadata:
            for item in metadata["Labels"]:
                try:
                    item["Operator"] = "generic_data_lookup"
                    item["Workflow"] = workflow
                    if "Label" in item:
                        # Flatten the inner Label array
                        item["Confidence"] = float(item["Label"]["Confidence"])*100
                        item["Name"] = item["Label"]["Name"]
                        item["Instances"] = ''
                        if 'Instances' in item["Label"]:
                            for box in item["Label"]["Instances"]:
                                box["BoundingBox"]["Height"] = float(box["BoundingBox"]["Height"]) / 720
                                box["BoundingBox"]["Top"] = float(box["BoundingBox"]["Top"]) / 720
                                box["BoundingBox"]["Left"] = float(box["BoundingBox"]["Left"]) / 1280
                                box["BoundingBox"]["Width"] = float(box["BoundingBox"]["Width"]) / 1280
                                box["Confidence"] = float(box["Confidence"])*100
                            item["Instances"] = item["Label"]["Instances"]
                        item["Parents"] = ''
                        if 'Parents' in item["Label"]:
                            item["Parents"] = item["Label"]["Parents"]
                        # Delete the flattened array
                        del item["Label"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
    bulk_index(es, asset, "labels", extracted_items)

def process_label_detection(asset, workflow, results):
    # Rekognition label detection puts labels on an inner array in its JSON result, but for ease of search in Elasticsearch we need those results as a top level json array. So this function does that.
    metadata = json.loads(results)
    es = connect_es(es_endpoint)
    extracted_items = []
    # We can tell if json results are paged by checking to see if the json results are an instance of the list type.
    if isinstance(metadata, list):
        # handle paged results
        for page in metadata:
            if "Labels" in page:
                for item in page["Labels"]:
                    try:
                        item["Operator"] = "label_detection"
                        item["Workflow"] = workflow
                        if "Label" in item:
                        # Flatten the inner Label array
                            item["Confidence"] = item["Label"]["Confidence"]
                            item["Name"] = item["Label"]["Name"]
                            item["Instances"] = ''
                            if 'Instances' in item["Label"]:
                                item["Instances"] = item["Label"]["Instances"]
                            item["Parents"] = ''
                            if 'Parents' in item["Label"]:
                                item["Parents"] = item["Label"]["Parents"]
                            # Delete the flattened array
                            del item["Label"]
                        extracted_items.append(item)
                    except KeyError as e:
                        print("KeyError: " + str(e))
                        print("Item: " + json.dumps(item))
    else:
        # these results are not paged
        if "Labels" in metadata:
            for item in metadata["Labels"]:
                try:
                    item["Operator"] = "label_detection"
                    item["Workflow"] = workflow
                    if "Label" in item:
                        # Flatten the inner Label array
                        item["Confidence"] = item["Label"]["Confidence"]
                        item["Name"] = item["Label"]["Name"]
                        item["Instances"] = ''
                        if 'Instances' in item["Label"]:
                            item["Instances"] = item["Label"]["Instances"]
                        item["Parents"] = ''
                        if 'Parents' in item["Label"]:
                            item["Parents"] = item["Label"]["Parents"]
                        # Delete the flattened array
                        del item["Label"]
                    extracted_items.append(item)
                except KeyError as e:
                    print("KeyError: " + str(e))
                    print("Item: " + json.dumps(item))
    bulk_index(es, asset, "labels", extracted_items)


def process_translate(asset, workflow, results):
    metadata = json.loads(results)

    translation = metadata
    translation["workflow"] = workflow
    es = connect_es(es_endpoint)
    index_document(es, asset, "translation", translation)


def process_transcribe(asset, workflow, results):
    metadata = json.loads(results)

    transcript = metadata["results"]["transcripts"][0]
    transcript["workflow"] = workflow
    transcript_time = metadata["results"]["items"]

    es = connect_es(es_endpoint)
    index_document(es, asset, "transcript", transcript)

    transcribe_items = []

    for item in transcript_time:
        content = item["alternatives"][0]["content"]
        confidence = normalize_confidence(item["alternatives"][0]["confidence"])
        if "start_time" in item and "end_time" in item:
            start_time = convert_to_milliseconds(item["start_time"])
            end_time = convert_to_milliseconds(item["end_time"])
            item["start_time"] = start_time
            item["end_time"] = end_time

        del item["alternatives"]

        item["confidence"] = confidence
        item["content"] = content
        item["workflow"] = workflow

        transcribe_items.append(item)

    bulk_index(es, asset, "transcriptiontime", transcribe_items)


def process_entities(asset, workflow, results):
    metadata = json.loads(results)
    entity_metadata = json.loads(metadata["Results"][0])
    entities = entity_metadata["Entities"]

    es = connect_es(es_endpoint)

    formatted_entities = []

    for entity in entities:
        entity["EntityType"] = entity["Type"]
        entity["EntityText"] = entity["Text"]

        confidence = normalize_confidence(entity["Score"])
        entity["Confidence"] = confidence

        entity["Workflow"] = workflow

        del entity["Type"]
        del entity["Text"]
        del entity["Score"]

        formatted_entities.append(entity)

    bulk_index(es, asset, "entities", formatted_entities)


def process_keyphrases(asset, workflow, results):
    metadata = json.loads(results)
    phrases_metadata = json.loads(metadata["Results"][0])
    phrases = phrases_metadata["KeyPhrases"]

    es = connect_es(es_endpoint)

    formatted_phrases = []

    for phrase in phrases:
        phrase["PhraseText"] = phrase["Text"]

        confidence = normalize_confidence(phrase["Score"])
        phrase["Confidence"] = confidence

        phrase["Workflow"] = workflow

        del phrase["Text"]
        del phrase["Score"]

        formatted_phrases.append(phrase)

    bulk_index(es, asset, "key_phrases", formatted_phrases)


def connect_es(endpoint):
    # Handle aws auth for es
    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, 'es',
                       session_token=credentials.token)
    print('Connecting to the ES Endpoint: {endpoint}'.format(endpoint=endpoint))
    try:
        es_client = Elasticsearch(
            hosts=[{'host': endpoint, 'port': 443}],
            use_ssl=True,
            verify_certs=True,
            http_auth=awsauth,
            connection_class=RequestsHttpConnection)
    except Exception as e:
        print("Unable to connect to {endpoint}:".format(endpoint=endpoint), e)
    else:
        print('Connected to elasticsearch')
        return es_client


def delete_asset_metadata_by_index(es_object, asset_id, index):
    try:
        es_object.delete(
            index=index,
            id=asset_id
        )
    except Exception as e:
        print("Unable to delete metadata from elasticsearch: {es}:".format(es=e))
    else:
        print("Deleted {asset} metadata: {index} rom elasticsearch".format(asset=asset_id, index=index))


def delete_asset_all_indices(es_object, asset_id):
    delete_query = {
      "query": {
        "match": {
          "AssetId": asset_id
        }
      }
    }

    try:
        delete_request = es_object.delete_by_query(
            index="_all",
            body=delete_query
        )
    except Exception as e:
        print("Unable to delete from elasticsearch: {es}:".format(es=e))
    else:
        print(delete_request)
        print("Deleted asset: {asset} from elasticsearch".format(asset=asset_id))


def bulk_index(es_object, asset, index, data):
    if len(data) == 0:
        print("Data is empty. Skipping insert to Elasticsearch.")
        return
    es_index = "mie{index}".format(index=index).lower()
    actions_to_send = []
    # Elasticsearch will respond with an error like, "Request size exceeded 10485760 bytes"
    # if the bulk insert exceeds a maximum payload size. To avoid that, we use a max payload
    # size that is well below the "Maximum Size of HTTP Request Payloads" for the smallest AWS
    # Elasticsearch instance type (10MB). See service limits here:
    # https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/aes-limits.html
    maxPayloadSize=8000000
    for item in data:
        item["AssetId"] = asset
        action = json.dumps({"index": {"_index": es_index, "_type": "_doc"}})
        doc = json.dumps(item)
        if ((len('\n'.join(actions_to_send))+len(action)+len(doc)) < maxPayloadSize):
            actions_to_send.append(action)
            actions_to_send.append(doc)
        else:
            # send and reset payload before appending the current item
            actions = '\n'.join(actions_to_send)
            print("bulk insert payload size: " + str(len(actions)))
            try:
                es_object.bulk(
                    index=es_index,
                    body=actions
                )
            except Exception as e:
                print('Unable to load data into es:', e)
                print("Data: ", item)
            else:
                print("Successfully stored data in elasticsearch for asset: ", asset)
            # now reset the payload and append the current item
            actions_to_send = []
            actions_to_send.append(action)
            actions_to_send.append(doc)
    # finally send the last item
    print("sending final bulk insert")
    actions = '\n'.join(actions_to_send)
    try:
        es_object.bulk(
            index=es_index,
            body=actions
        )
    except Exception as e:
        print('Unable to load data into es:', e)
        print("Data: ", data)
    else:
        print("Successfully stored data in elasticsearch for asset: ", asset)


def index_document(es_object, asset, index, data):
    es_index = "mie{index}".format(index=index).lower()
    data["AssetId"] = asset
    try:
        es_object.index(
            index=es_index,
            body=data,
            request_timeout=30
        )
    except Exception as e:
        print('Unable to load data into es:', e)
        print("Data:", data)
    else:
        print("Successfully stored data in elasticsearch for:", asset)


def read_json_from_s3(key):
    bucket = dataplane_bucket
    try:
        obj = s3.get_object(
            Bucket=bucket,
            Key=key
        )
    except Exception as e:
        return {"Status": "Error", "Error": e}
    else:
        results = obj['Body'].read().decode('utf-8')
        return {"Status": "Success", "Results": results}


def lambda_handler(event, context):
    print("Received event:", event)

    action = None
    asset_id = None
    payload = None

    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        try:
            asset_id = record['kinesis']['partitionKey']
            payload = json.loads(base64.b64decode(record["kinesis"]["data"]))
        except Exception as e:
            print("Error decoding kinesis event", e)
        else:
            print("Decoded payload for asset:", asset_id)
            try:
                action = payload['Action']
            except KeyError as e:
                print("Missing action type from kinesis record:", e)
            else:
                print("Attempting the following action:", action)

        if action is None:
            print("Unable to determine action type")
        elif action == "INSERT":
            print("Not handling INSERT actions")
        elif action == "MODIFY":
            try:
                operator = payload['Operator']
                s3_pointer = payload['Pointer']
                workflow = payload['Workflow']
            except KeyError as e:
                print("Missing required keys in kinesis payload:", e)
            else:
                # Read in json metadata from s3
                metadata = read_json_from_s3(s3_pointer)
                if metadata["Status"] == "Success":
                    print("Retrieved {operator} metadata from s3, inserting into Elasticsearch".format(operator=operator))
                    operator = operator.lower()
                    # Route event to process method based on the operator type in the event.
                    # These names are the lowercase version of OPERATOR_NAME defined in /source/operators/operator-library.yaml
                    if operator in supported_operators:
                        if operator == "transcribe":
                            process_transcribe(asset_id, workflow, metadata["Results"])
                        if operator == "translate":
                            process_translate(asset_id, workflow, metadata["Results"])
                        if operator == "mediainfo":
                            process_mediainfo(asset_id, workflow, metadata["Results"])
                        if operator == "genericdatalookup":
                            process_generic_data(asset_id, workflow, metadata["Results"])
                        if operator == "labeldetection":
                            process_label_detection(asset_id, workflow, metadata["Results"])
                        if operator == "celebrityrecognition":
                            process_celebrity_detection(asset_id, workflow, metadata["Results"])
                        if operator == "contentmoderation":
                            process_content_moderation(asset_id, workflow, metadata["Results"])
                        if operator == "facedetection":
                            process_face_detection(asset_id, workflow, metadata["Results"])
                        if operator == "facesearch":
                            process_face_search(asset_id, workflow, metadata["Results"])
                        if operator == "entities":
                            process_entities(asset_id, workflow, metadata["Results"])
                        if operator == "key_phrases":
                            process_keyphrases(asset_id, workflow, metadata["Results"])
                        if operator == "textdetection":
                            process_text_detection(asset_id, workflow, metadata["Results"])
                    else:
                        print("We do not store {operator} results".format(operator=operator))
                else:
                    print("Unable to read metadata from s3: {e}".format(e=metadata["Error"]))
        elif action == "REMOVE":
            try:
                operator = payload['Operator']
            except KeyError:
                print("Operator type not present in payload, this must be a request to delete the entire asset")
                es = connect_es(es_endpoint)
                delete_asset_all_indices(es, asset_id)
            else:
                print(payload)
                print('Not allowing deletion of specific metadata from ES as that is not exposed in the UI')
                # print("Deleting {operator} metadata for asset {asset}".format(operator=operator, asset=asset_id))
                # es = connect_es(es_endpoint)
                # delete_asset_metadata_by_index(es, asset_id, operator)
