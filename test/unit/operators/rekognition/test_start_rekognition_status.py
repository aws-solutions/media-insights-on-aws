from start_rekognition_test_tool import StartRekognitionTestTool

def test_check_content_moderation_status():
    import rekognition.start_celebrity_recognition as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'CelebrityRecognitionError',
        'recognize_celebrities',
        'start_celebrity_recognition'
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_content_moderation():
    import rekognition.start_content_moderation as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'ContentModerationError',
        'detect_moderation_labels',
        'start_content_moderation'
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_face_detection():
    import rekognition.start_face_detection as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    def video_stub_function(stub):
        stub.add_response(
            'start_face_detection',
            expected_params = {
                'Video': {
                    'S3Object': {
                        'Bucket': 'test_bucket',
                        'Name': 'test_key.mp4'
                    }
                },
                'NotificationChannel': {
                    'SNSTopicArn': 'testRekognitionSNSTopicArn',
                    'RoleArn': 'testRekognitionRoleArn'
                },
                'FaceAttributes': 'ALL'
            },
            service_response = {'JobId': 'testJobId'}
        )

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'FaceDetectionError',
        'detect_faces',
        'start_face_detection',
        None,
        video_stub_function
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_face_search():
    import rekognition.start_face_search as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    def image_stub_function(stub):
        stub.add_response(
            'search_faces_by_image',
            expected_params = {
                'CollectionId': 'testCollectionId',
                'Image': {
                    'S3Object': {
                        'Bucket': 'test_bucket',
                        'Name': 'test_key.png'
                    }
                }
            },
            service_response = {}
        )
    
    def video_stub_function(stub):
        stub.add_response(
            'describe_collection',
            expected_params = {'CollectionId': 'testCollectionId'},
            service_response = {}
        )
        stub.add_response(
            'start_face_search',
            expected_params = {
                'Video': {
                    'S3Object': {
                        'Bucket': 'test_bucket',
                        'Name': 'test_key.mp4'
                    }
                },
                'CollectionId': 'testCollectionId',
                'NotificationChannel': {
                    'SNSTopicArn': 'testRekognitionSNSTopicArn',
                    'RoleArn': 'testRekognitionRoleArn'
                }
            },
            service_response = {
                'JobId': 'testJobId'
            }
        )

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'FaceSearchError',
        'search_faces_by_image',
        'start_face_search',
        image_stub_function,
        video_stub_function
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_label_detection():
    import rekognition.start_label_detection as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'LabelDetectionError',
        'detect_labels',
        'start_label_detection'
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_shot_detection():
    import rekognition.start_shot_detection as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    def video_stub_function(stub):
        stub.add_response(
            'start_segment_detection',
            expected_params = {
                'Video': {
                    'S3Object': {
                        'Bucket': 'test_bucket',
                        'Name': 'test_key.mp4'
                    }
                },
                'NotificationChannel': {
                    'SNSTopicArn': 'testRekognitionSNSTopicArn',
                    'RoleArn': 'testRekognitionRoleArn'
                },
                'SegmentTypes': ['SHOT']
            },
            service_response = {'JobId': 'testJobId'}
        )

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'LabelDetectionError',
        'detect_labels',
        'start_segment_detection',
        None,
        video_stub_function
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e

def test_start_text_detection():
    import rekognition.start_text_detection as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    test_tool = StartRekognitionTestTool(
        lambda_function,
        MediaInsightsEngineLambdaHelper.MasExecutionError,
        helper,
        'TextDetectionError',
        'detect_text',
        'start_text_detection'
    )
    try:
        test_tool.run_tests()
    except AssertionError as assertion_error:
        raise assertion_error
    except Exception as e:
        raise e
