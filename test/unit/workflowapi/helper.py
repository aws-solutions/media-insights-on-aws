import botocore.stub
import json

test_operation_name = 'testOperationName'

def get_sample_workflow_output():
    return {
        "ApiVersion": {
            "S": "3.0.0"
        },
        "Created": {
            "S": "1605822398.292371"
        },
        "Id": {
            "S": "90c25511-72e4-4220-885a-d36e5dbb0c88"
        },
        "Name": {
            "S": "CasVideoWorkflow"
        },
        "Operations": {
            "L": [
                {
                    "S": "Thumbnail"
                },
                {
                    "S": "Mediainfo"
                },
                {
                    "S": "GenericDataLookup"
                },
                {
                    "S": "celebrityRecognition"
                },
                {
                    "S": "contentModeration"
                },
                {
                    "S": "faceDetection"
                },
                {
                    "S": "faceSearch"
                },
                {
                    "S": "labelDetection"
                },
                {
                    "S": "personTracking"
                },
                {
                    "S": "textDetection"
                },
                {
                    "S": "Mediaconvert"
                },
                {
                    "S": "technicalCueDetection"
                },
                {
                    "S": "shotDetection"
                },
                {
                    "S": "Transcribe"
                },
                {
                    "S": "Translate"
                },
                {
                    "S": "ComprehendKeyPhrases"
                },
                {
                    "S": "ComprehendEntities"
                },
                {
                    "S": "Polly"
                }
            ]
        },
        "ResourceType": {
            "S": "WORKFLOW"
        },
        "Revisions": {
            "S": "1"
        },
        "ServiceToken": {
            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
        },
        "Stages": {
            "M": {
                "defaultAudioStage": {
                    "M": {
                        "ApiVersion": {
                            "S": "3.0.0"
                        },
                        "Configuration": {
                            "M": {
                                "Transcribe": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Audio"
                                        },
                                        "TranscribeLanguage": {
                                            "S": "en-US"
                                        }
                                    }
                                }
                            }
                        },
                        "Created": {
                            "S": "1605822392.347856"
                        },
                        "Definition": {
                            "S": "{\"StartAt\": \"defaultAudioStage\", \"States\": {\"Complete Stage defaultAudioStage\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"defaultAudioStage\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage defaultAudioStage\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Transcribe Media Type? (defaultAudioStage)\", \"States\": {\"Filter Transcribe Media Type? (defaultAudioStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Transcribe\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Transcribe\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Audio\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Transcribe? (defaultAudioStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (defaultAudioStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Transcribe? (defaultAudioStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Transcribe (defaultAudioStage)\"}], \"Default\": \"Transcribe Not Started (defaultAudioStage)\"}, \"Transcribe Not Started (defaultAudioStage)\": {\"Type\": \"Succeed\"}, \"Execute Transcribe (defaultAudioStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-StartTranscribeFunction-153XYIT0IY722\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Transcribe Wait (defaultAudioStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (defaultAudioStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Transcribe Wait (defaultAudioStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Transcribe Status (defaultAudioStage)\"}, \"Get Transcribe Status (defaultAudioStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-CheckTranscribeFunction-89O51Q3AA9L8\", \"Next\": \"Did Transcribe Complete (defaultAudioStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (defaultAudioStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Transcribe Complete (defaultAudioStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Transcribe Wait (defaultAudioStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Transcribe Succeeded (defaultAudioStage)\"}], \"Default\": \"Transcribe Failed (defaultAudioStage)\"}, \"Transcribe Failed (defaultAudioStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Transcribe Succeeded (defaultAudioStage)\": {\"Type\": \"Succeed\"}}}]}}}"
                        },
                        "Id": {
                            "S": "9c593fe6-87da-4765-918e-35d1f0f7cd5d"
                        },
                        "Name": {
                            "S": "defaultAudioStage"
                        },
                        "Next": {
                            "S": "defaultTextStage"
                        },
                        "Operations": {
                            "L": [
                                {
                                    "S": "Transcribe"
                                }
                            ]
                        },
                        "ResourceType": {
                            "S": "STAGE"
                        },
                        "ServiceToken": {
                            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
                        },
                        "Version": {
                            "S": "v0"
                        }
                    }
                },
                "defaultPrelimVideoStage": {
                    "M": {
                        "ApiVersion": {
                            "S": "3.0.0"
                        },
                        "Configuration": {
                            "M": {
                                "Mediainfo": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "Thumbnail": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                }
                            }
                        },
                        "Created": {
                            "S": "1605822392.5396"
                        },
                        "Definition": {
                            "S": "{\"StartAt\": \"defaultPrelimVideoStage\", \"States\": {\"Complete Stage defaultPrelimVideoStage\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"defaultPrelimVideoStage\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage defaultPrelimVideoStage\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Thumbnail Media Type? (defaultPrelimVideoStage)\", \"States\": {\"Filter Thumbnail Media Type? (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Thumbnail\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Thumbnail\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Thumbnail? (defaultPrelimVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (defaultPrelimVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Thumbnail? (defaultPrelimVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Thumbnail (defaultPrelimVideoStage)\"}], \"Default\": \"Thumbnail Not Started (defaultPrelimVideoStage)\"}, \"Thumbnail Not Started (defaultPrelimVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute Thumbnail (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-StartThumbnailFunction-Z3SEQQ2SOMIP\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Thumbnail Wait (defaultPrelimVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (defaultPrelimVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Thumbnail Wait (defaultPrelimVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Thumbnail Status (defaultPrelimVideoStage)\"}, \"Get Thumbnail Status (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-CheckThumbnailFunction-1HYU14L5W9F6S\", \"Next\": \"Did Thumbnail Complete (defaultPrelimVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (defaultPrelimVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Thumbnail Complete (defaultPrelimVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Thumbnail Wait (defaultPrelimVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Thumbnail Succeeded (defaultPrelimVideoStage)\"}], \"Default\": \"Thumbnail Failed (defaultPrelimVideoStage)\"}, \"Thumbnail Failed (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Thumbnail Succeeded (defaultPrelimVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter Mediainfo Media Type? (defaultPrelimVideoStage)\", \"States\": {\"Filter Mediainfo Media Type? (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Mediainfo\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Mediainfo\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Mediainfo? (defaultPrelimVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediainfo Failed (defaultPrelimVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Mediainfo? (defaultPrelimVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Mediainfo (defaultPrelimVideoStage)\"}], \"Default\": \"Mediainfo Not Started (defaultPrelimVideoStage)\"}, \"Mediainfo Not Started (defaultPrelimVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute Mediainfo (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-Mediainfo-1DVF30BM43KO\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Did Mediainfo Complete (defaultPrelimVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediainfo Failed (defaultPrelimVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Mediainfo Complete (defaultPrelimVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Mediainfo Succeeded (defaultPrelimVideoStage)\"}], \"Default\": \"Mediainfo Failed (defaultPrelimVideoStage)\"}, \"Mediainfo Failed (defaultPrelimVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Mediainfo Succeeded (defaultPrelimVideoStage)\": {\"Type\": \"Succeed\"}}}]}}}"
                        },
                        "Id": {
                            "S": "9c3d95b9-e266-483c-bd68-a3821cca200f"
                        },
                        "Name": {
                            "S": "defaultPrelimVideoStage"
                        },
                        "Next": {
                            "S": "defaultVideoStage"
                        },
                        "Operations": {
                            "L": [
                                {
                                    "S": "Thumbnail"
                                },
                                {
                                    "S": "Mediainfo"
                                }
                            ]
                        },
                        "ResourceType": {
                            "S": "STAGE"
                        },
                        "ServiceToken": {
                            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
                        },
                        "Version": {
                            "S": "v0"
                        }
                    }
                },
                "defaultTextStage": {
                    "M": {
                        "ApiVersion": {
                            "S": "3.0.0"
                        },
                        "Configuration": {
                            "M": {
                                "ComprehendEntities": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Text"
                                        }
                                    }
                                },
                                "ComprehendKeyPhrases": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Text"
                                        }
                                    }
                                },
                                "Translate": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Text"
                                        },
                                        "SourceLanguageCode": {
                                            "S": "en"
                                        },
                                        "TargetLanguageCode": {
                                            "S": "ru"
                                        }
                                    }
                                }
                            }
                        },
                        "Created": {
                            "S": "1605822392.521437"
                        },
                        "Definition": {
                            "S": "{\"StartAt\": \"defaultTextStage\", \"States\": {\"Complete Stage defaultTextStage\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"defaultTextStage\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage defaultTextStage\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Translate Media Type? (defaultTextStage)\", \"States\": {\"Filter Translate Media Type? (defaultTextStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Translate\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Translate\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Translate? (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Translate Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Translate? (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Translate (defaultTextStage)\"}], \"Default\": \"Translate Not Started (defaultTextStage)\"}, \"Translate Not Started (defaultTextStage)\": {\"Type\": \"Succeed\"}, \"Execute Translate (defaultTextStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-TranslateFunction-BQDTYMDCCWBQ\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Did Translate Complete (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Translate Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Translate Complete (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Translate Succeeded (defaultTextStage)\"}], \"Default\": \"Translate Failed (defaultTextStage)\"}, \"Translate Failed (defaultTextStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Translate Succeeded (defaultTextStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter ComprehendKeyPhrases Media Type? (defaultTextStage)\", \"States\": {\"Filter ComprehendKeyPhrases Media Type? (defaultTextStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"ComprehendKeyPhrases\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.ComprehendKeyPhrases\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip ComprehendKeyPhrases? (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip ComprehendKeyPhrases? (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute ComprehendKeyPhrases (defaultTextStage)\"}], \"Default\": \"ComprehendKeyPhrases Not Started (defaultTextStage)\"}, \"ComprehendKeyPhrases Not Started (defaultTextStage)\": {\"Type\": \"Succeed\"}, \"Execute ComprehendKeyPhrases (defaultTextStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-startKeyPhrases-HBO46ZS9TUR2\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"ComprehendKeyPhrases Wait (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"ComprehendKeyPhrases Wait (defaultTextStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get ComprehendKeyPhrases Status (defaultTextStage)\"}, \"Get ComprehendKeyPhrases Status (defaultTextStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-getKeyPhrases-142K58QL4DLFH\", \"Next\": \"Did ComprehendKeyPhrases Complete (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did ComprehendKeyPhrases Complete (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"ComprehendKeyPhrases Wait (defaultTextStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"ComprehendKeyPhrases Succeeded (defaultTextStage)\"}], \"Default\": \"ComprehendKeyPhrases Failed (defaultTextStage)\"}, \"ComprehendKeyPhrases Failed (defaultTextStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"ComprehendKeyPhrases Succeeded (defaultTextStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter ComprehendEntities Media Type? (defaultTextStage)\", \"States\": {\"Filter ComprehendEntities Media Type? (defaultTextStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"ComprehendEntities\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.ComprehendEntities\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip ComprehendEntities? (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip ComprehendEntities? (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute ComprehendEntities (defaultTextStage)\"}], \"Default\": \"ComprehendEntities Not Started (defaultTextStage)\"}, \"ComprehendEntities Not Started (defaultTextStage)\": {\"Type\": \"Succeed\"}, \"Execute ComprehendEntities (defaultTextStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQ-startEntityDetection-1JLL7TLKMEPLQ\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"ComprehendEntities Wait (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"ComprehendEntities Wait (defaultTextStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get ComprehendEntities Status (defaultTextStage)\"}, \"Get ComprehendEntities Status (defaultTextStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-getEntityDetection-AU3SRAKKGKR1\", \"Next\": \"Did ComprehendEntities Complete (defaultTextStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (defaultTextStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did ComprehendEntities Complete (defaultTextStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"ComprehendEntities Wait (defaultTextStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"ComprehendEntities Succeeded (defaultTextStage)\"}], \"Default\": \"ComprehendEntities Failed (defaultTextStage)\"}, \"ComprehendEntities Failed (defaultTextStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"ComprehendEntities Succeeded (defaultTextStage)\": {\"Type\": \"Succeed\"}}}]}}}"
                        },
                        "Id": {
                            "S": "7ce14df6-6691-4333-8108-951c6ce2f588"
                        },
                        "Name": {
                            "S": "defaultTextStage"
                        },
                        "Next": {
                            "S": "defaultTextSynthesisStage"
                        },
                        "Operations": {
                            "L": [
                                {
                                    "S": "Translate"
                                },
                                {
                                    "S": "ComprehendKeyPhrases"
                                },
                                {
                                    "S": "ComprehendEntities"
                                }
                            ]
                        },
                        "ResourceType": {
                            "S": "STAGE"
                        },
                        "ServiceToken": {
                            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
                        },
                        "Version": {
                            "S": "v0"
                        }
                    }
                },
                "defaultTextSynthesisStage": {
                    "M": {
                        "ApiVersion": {
                            "S": "3.0.0"
                        },
                        "Configuration": {
                            "M": {
                                "Polly": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Text"
                                        }
                                    }
                                }
                            }
                        },
                        "Created": {
                            "S": "1605822392.29234"
                        },
                        "Definition": {
                            "S": "{\"StartAt\": \"defaultTextSynthesisStage\", \"States\": {\"Complete Stage defaultTextSynthesisStage\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"defaultTextSynthesisStage\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage defaultTextSynthesisStage\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Polly Media Type? (defaultTextSynthesisStage)\", \"States\": {\"Filter Polly Media Type? (defaultTextSynthesisStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Polly\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Polly\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Polly? (defaultTextSynthesisStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Polly Failed (defaultTextSynthesisStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Polly? (defaultTextSynthesisStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Polly (defaultTextSynthesisStage)\"}], \"Default\": \"Polly Not Started (defaultTextSynthesisStage)\"}, \"Polly Not Started (defaultTextSynthesisStage)\": {\"Type\": \"Succeed\"}, \"Execute Polly (defaultTextSynthesisStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-StartPollyFunction-KMVDA4PPE90D\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Polly Wait (defaultTextSynthesisStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Polly Failed (defaultTextSynthesisStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Polly Wait (defaultTextSynthesisStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Polly Status (defaultTextSynthesisStage)\"}, \"Get Polly Status (defaultTextSynthesisStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-CheckPollyFunction-1MCR9QKJ9SQ11\", \"Next\": \"Did Polly Complete (defaultTextSynthesisStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Polly Failed (defaultTextSynthesisStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Polly Complete (defaultTextSynthesisStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Polly Wait (defaultTextSynthesisStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Polly Succeeded (defaultTextSynthesisStage)\"}], \"Default\": \"Polly Failed (defaultTextSynthesisStage)\"}, \"Polly Failed (defaultTextSynthesisStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Polly Succeeded (defaultTextSynthesisStage)\": {\"Type\": \"Succeed\"}}}]}}}"
                        },
                        "End": {
                            "BOOL": True
                        },
                        "Id": {
                            "S": "9d5fcb7d-d8aa-4583-ba88-2f7e01c7f662"
                        },
                        "Name": {
                            "S": "defaultTextSynthesisStage"
                        },
                        "Operations": {
                            "L": [
                                {
                                    "S": "Polly"
                                }
                            ]
                        },
                        "ResourceType": {
                            "S": "STAGE"
                        },
                        "ServiceToken": {
                            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
                        },
                        "Version": {
                            "S": "v0"
                        }
                    }
                },
                "defaultVideoStage": {
                    "M": {
                        "ApiVersion": {
                            "S": "3.0.0"
                        },
                        "Configuration": {
                            "M": {
                                "celebrityRecognition": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "contentModeration": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "faceDetection": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "faceSearch": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "GenericDataLookup": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "labelDetection": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "Mediaconvert": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "personTracking": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "shotDetection": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "technicalCueDetection": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                },
                                "textDetection": {
                                    "M": {
                                        "Enabled": {
                                            "BOOL": True
                                        },
                                        "MediaType": {
                                            "S": "Video"
                                        }
                                    }
                                }
                            }
                        },
                        "Created": {
                            "S": "1605822393.258908"
                        },
                        "Definition": {
                            "S": "{\"StartAt\": \"defaultVideoStage\", \"States\": {\"Complete Stage defaultVideoStage\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"defaultVideoStage\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage defaultVideoStage\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter GenericDataLookup Media Type? (defaultVideoStage)\", \"States\": {\"Filter GenericDataLookup Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"GenericDataLookup\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.GenericDataLookup\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip GenericDataLookup? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"GenericDataLookup Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip GenericDataLookup? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute GenericDataLookup (defaultVideoStage)\"}], \"Default\": \"GenericDataLookup Not Started (defaultVideoStage)\"}, \"GenericDataLookup Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute GenericDataLookup (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-startGenericDataLookup-13CEX0QWQY9J7\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Did GenericDataLookup Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"GenericDataLookup Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did GenericDataLookup Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"GenericDataLookup Succeeded (defaultVideoStage)\"}], \"Default\": \"GenericDataLookup Failed (defaultVideoStage)\"}, \"GenericDataLookup Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"GenericDataLookup Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter celebrityRecognition Media Type? (defaultVideoStage)\", \"States\": {\"Filter celebrityRecognition Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"celebrityRecognition\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.celebrityRecognition\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip celebrityRecognition? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip celebrityRecognition? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute celebrityRecognition (defaultVideoStage)\"}], \"Default\": \"celebrityRecognition Not Started (defaultVideoStage)\"}, \"celebrityRecognition Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute celebrityRecognition (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startCelebrityRecognitio-1D14BTFUME8KK\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"celebrityRecognition Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"celebrityRecognition Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get celebrityRecognition Status (defaultVideoStage)\"}, \"Get celebrityRecognition Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkCelebrityRecognitio-CNFP2WPPNNTY\", \"Next\": \"Did celebrityRecognition Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did celebrityRecognition Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"celebrityRecognition Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"celebrityRecognition Succeeded (defaultVideoStage)\"}], \"Default\": \"celebrityRecognition Failed (defaultVideoStage)\"}, \"celebrityRecognition Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"celebrityRecognition Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter contentModeration Media Type? (defaultVideoStage)\", \"States\": {\"Filter contentModeration Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"contentModeration\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.contentModeration\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip contentModeration? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip contentModeration? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute contentModeration (defaultVideoStage)\"}], \"Default\": \"contentModeration Not Started (defaultVideoStage)\"}, \"contentModeration Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute contentModeration (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-startContentModeration-1SOB9NPL9OU21\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"contentModeration Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"contentModeration Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get contentModeration Status (defaultVideoStage)\"}, \"Get contentModeration Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-checkContentModeration-1WQMPJWYG335Y\", \"Next\": \"Did contentModeration Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did contentModeration Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"contentModeration Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"contentModeration Succeeded (defaultVideoStage)\"}], \"Default\": \"contentModeration Failed (defaultVideoStage)\"}, \"contentModeration Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"contentModeration Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter faceDetection Media Type? (defaultVideoStage)\", \"States\": {\"Filter faceDetection Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"faceDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.faceDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip faceDetection? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip faceDetection? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute faceDetection (defaultVideoStage)\"}], \"Default\": \"faceDetection Not Started (defaultVideoStage)\"}, \"faceDetection Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute faceDetection (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startFaceDetection-4YGNSMCBZRVE\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"faceDetection Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"faceDetection Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get faceDetection Status (defaultVideoStage)\"}, \"Get faceDetection Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkFaceDetection-1GYB309627Y2H\", \"Next\": \"Did faceDetection Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did faceDetection Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"faceDetection Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"faceDetection Succeeded (defaultVideoStage)\"}], \"Default\": \"faceDetection Failed (defaultVideoStage)\"}, \"faceDetection Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"faceDetection Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter faceSearch Media Type? (defaultVideoStage)\", \"States\": {\"Filter faceSearch Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"faceSearch\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.faceSearch\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip faceSearch? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceSearch Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip faceSearch? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute faceSearch (defaultVideoStage)\"}], \"Default\": \"faceSearch Not Started (defaultVideoStage)\"}, \"faceSearch Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute faceSearch (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-startFaceSearch-1IZHRQVB9NZL6\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"faceSearch Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceSearch Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"faceSearch Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get faceSearch Status (defaultVideoStage)\"}, \"Get faceSearch Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-checkFaceSearch-ZQN9SPW3H754\", \"Next\": \"Did faceSearch Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceSearch Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did faceSearch Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"faceSearch Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"faceSearch Succeeded (defaultVideoStage)\"}], \"Default\": \"faceSearch Failed (defaultVideoStage)\"}, \"faceSearch Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"faceSearch Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter labelDetection Media Type? (defaultVideoStage)\", \"States\": {\"Filter labelDetection Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"labelDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.labelDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip labelDetection? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip labelDetection? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute labelDetection (defaultVideoStage)\"}], \"Default\": \"labelDetection Not Started (defaultVideoStage)\"}, \"labelDetection Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute labelDetection (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startLabelDetection-125TMWFXWCDUW\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"labelDetection Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"labelDetection Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get labelDetection Status (defaultVideoStage)\"}, \"Get labelDetection Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkLabelDetection-1TJTKK0SC9ABR\", \"Next\": \"Did labelDetection Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did labelDetection Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"labelDetection Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"labelDetection Succeeded (defaultVideoStage)\"}], \"Default\": \"labelDetection Failed (defaultVideoStage)\"}, \"labelDetection Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"labelDetection Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter personTracking Media Type? (defaultVideoStage)\", \"States\": {\"Filter personTracking Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"personTracking\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.personTracking\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip personTracking? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip personTracking? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute personTracking (defaultVideoStage)\"}], \"Default\": \"personTracking Not Started (defaultVideoStage)\"}, \"personTracking Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute personTracking (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startPersonTracking-113JL6LE8X356\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"personTracking Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"personTracking Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get personTracking Status (defaultVideoStage)\"}, \"Get personTracking Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkPersonTracking-1HD4C4PV511CU\", \"Next\": \"Did personTracking Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did personTracking Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"personTracking Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"personTracking Succeeded (defaultVideoStage)\"}], \"Default\": \"personTracking Failed (defaultVideoStage)\"}, \"personTracking Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"personTracking Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter textDetection Media Type? (defaultVideoStage)\", \"States\": {\"Filter textDetection Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"textDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.textDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip textDetection? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip textDetection? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute textDetection (defaultVideoStage)\"}], \"Default\": \"textDetection Not Started (defaultVideoStage)\"}, \"textDetection Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute textDetection (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startTextDetection-1VKG25EE66L1I\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"textDetection Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"textDetection Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get textDetection Status (defaultVideoStage)\"}, \"Get textDetection Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkTextDetection-1I7WEG7QGZLS0\", \"Next\": \"Did textDetection Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did textDetection Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"textDetection Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"textDetection Succeeded (defaultVideoStage)\"}], \"Default\": \"textDetection Failed (defaultVideoStage)\"}, \"textDetection Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"textDetection Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter Mediaconvert Media Type? (defaultVideoStage)\", \"States\": {\"Filter Mediaconvert Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Mediaconvert\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Mediaconvert\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Mediaconvert? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Mediaconvert? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Mediaconvert (defaultVideoStage)\"}], \"Default\": \"Mediaconvert Not Started (defaultVideoStage)\"}, \"Mediaconvert Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute Mediaconvert (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-StartMediaConvertFunctio-X0UUOJVL6AX2\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Mediaconvert Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Mediaconvert Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Mediaconvert Status (defaultVideoStage)\"}, \"Get Mediaconvert Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-CheckMediaConvertFunctio-1W0HFF4G4AYSD\", \"Next\": \"Did Mediaconvert Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Mediaconvert Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Mediaconvert Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Mediaconvert Succeeded (defaultVideoStage)\"}], \"Default\": \"Mediaconvert Failed (defaultVideoStage)\"}, \"Mediaconvert Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Mediaconvert Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter technicalCueDetection Media Type? (defaultVideoStage)\", \"States\": {\"Filter technicalCueDetection Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"technicalCueDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.technicalCueDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip technicalCueDetection? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip technicalCueDetection? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute technicalCueDetection (defaultVideoStage)\"}], \"Default\": \"technicalCueDetection Not Started (defaultVideoStage)\"}, \"technicalCueDetection Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute technicalCueDetection (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startTechnicalCueDetecti-1NWCRDJLZP5LV\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"technicalCueDetection Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"technicalCueDetection Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get technicalCueDetection Status (defaultVideoStage)\"}, \"Get technicalCueDetection Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkTechnicalCueDetecti-QY16N45OC9SS\", \"Next\": \"Did technicalCueDetection Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did technicalCueDetection Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"technicalCueDetection Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"technicalCueDetection Succeeded (defaultVideoStage)\"}], \"Default\": \"technicalCueDetection Failed (defaultVideoStage)\"}, \"technicalCueDetection Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"technicalCueDetection Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter shotDetection Media Type? (defaultVideoStage)\", \"States\": {\"Filter shotDetection Media Type? (defaultVideoStage)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"shotDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.shotDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip shotDetection? (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip shotDetection? (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute shotDetection (defaultVideoStage)\"}], \"Default\": \"shotDetection Not Started (defaultVideoStage)\"}, \"shotDetection Not Started (defaultVideoStage)\": {\"Type\": \"Succeed\"}, \"Execute shotDetection (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startShotDetection-1Q2DLD30UC91V\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"shotDetection Wait (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"shotDetection Wait (defaultVideoStage)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get shotDetection Status (defaultVideoStage)\"}, \"Get shotDetection Status (defaultVideoStage)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkShotDetection-18OOGE8QDQO2W\", \"Next\": \"Did shotDetection Complete (defaultVideoStage)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (defaultVideoStage)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did shotDetection Complete (defaultVideoStage)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"shotDetection Wait (defaultVideoStage)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"shotDetection Succeeded (defaultVideoStage)\"}], \"Default\": \"shotDetection Failed (defaultVideoStage)\"}, \"shotDetection Failed (defaultVideoStage)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"shotDetection Succeeded (defaultVideoStage)\": {\"Type\": \"Succeed\"}}}]}}}"
                        },
                        "Id": {
                            "S": "dca4038a-7ac7-41e9-8044-76bed36d2c9f"
                        },
                        "Name": {
                            "S": "defaultVideoStage"
                        },
                        "Next": {
                            "S": "defaultAudioStage"
                        },
                        "Operations": {
                            "L": [
                                {
                                    "S": "GenericDataLookup"
                                },
                                {
                                    "S": "celebrityRecognition"
                                },
                                {
                                    "S": "contentModeration"
                                },
                                {
                                    "S": "faceDetection"
                                },
                                {
                                    "S": "faceSearch"
                                },
                                {
                                    "S": "labelDetection"
                                },
                                {
                                    "S": "personTracking"
                                },
                                {
                                    "S": "textDetection"
                                },
                                {
                                    "S": "Mediaconvert"
                                },
                                {
                                    "S": "technicalCueDetection"
                                },
                                {
                                    "S": "shotDetection"
                                }
                            ]
                        },
                        "ResourceType": {
                            "S": "STAGE"
                        },
                        "ServiceToken": {
                            "S": "arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD"
                        },
                        "Version": {
                            "S": "v0"
                        }
                    }
                }
            }
        },
        "StaleOperations": {
            "L": [

            ]
        },
        "StaleStages": {
            "L": [

            ]
        },
        "StartAt": {
            "S": "defaultPrelimVideoStage"
        },
        "StateMachineArn": {
            "S": "arn:aws:states:us-west-2:123456789:stateMachine:CasVideoWorkflow-aqx5d8"
        },
        "Trigger": {
            "S": "custom-resource"
        },
        "Version": {
            "S": "v0"
        }
    }

sample_workflow_execution = {
    'Id': botocore.stub.ANY,
    'Trigger': 'api',
    'CurrentStage': 'defaultPrelimVideoStage',
    'Globals': {
        'Media': {
            'Video': {
                'S3Bucket': 'testBucket',
                'S3Key': 'private/assets/abcd-1234-efgh/input/testFile.mp4'
            }
        },
        'MetaData': {}
    },
    'Configuration': {},
    'AssetId': 'abcd-1234-efgh',
    'Version': 'v0',
    'Created': botocore.stub.ANY,
    'ResourceType': 'WORKFLOW_EXECUTION',
    'ApiVersion': '3.0.0',
    'Workflow': {
        'ApiVersion': '3.0.0',
        'Created': '1605822398.292371',
        'Id': '90c25511-72e4-4220-885a-d36e5dbb0c88',
        'Name': 'CasVideoWorkflow',
        'Operations': ['Thumbnail', 'Mediainfo', 'GenericDataLookup', 'celebrityRecognition', 'contentModeration',
                       'faceDetection', 'faceSearch', 'labelDetection', 'personTracking', 'textDetection',
                       'Mediaconvert', 'technicalCueDetection', 'shotDetection', 'Transcribe', 'Translate',
                       'ComprehendKeyPhrases', 'ComprehendEntities', 'Polly'],
        'ResourceType': 'WORKFLOW',
        'Revisions': '1',
        'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
        'Stages': {
            'defaultAudioStage': {
                'ApiVersion': '3.0.0',
                'Configuration': {
                    'Transcribe': {
                        'Enabled': True,
                        'MediaType': 'Audio',
                        'TranscribeLanguage': 'en-US'
                    }
                },
                'Created': '1605822392.347856',
                'Definition': '{"StartAt": "defaultAudioStage", "States": {"Complete Stage defaultAudioStage": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G", "End": True}, "defaultAudioStage": {"Type": "Parallel", "Next": "Complete Stage defaultAudioStage", "ResultPath": "$.Outputs", "Branches": [{"StartAt": "Filter Transcribe Media Type? (defaultAudioStage)", "States": {"Filter Transcribe Media Type? (defaultAudioStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Transcribe", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Transcribe", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Audio", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Transcribe? (defaultAudioStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Transcribe Failed (defaultAudioStage)", "ResultPath": "$.Outputs"}]}, "Skip Transcribe? (defaultAudioStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Transcribe (defaultAudioStage)"}], "Default": "Transcribe Not Started (defaultAudioStage)"}, "Transcribe Not Started (defaultAudioStage)": {"Type": "Succeed"}, "Execute Transcribe (defaultAudioStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-StartTranscribeFunction-153XYIT0IY722", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Transcribe Wait (defaultAudioStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Transcribe Failed (defaultAudioStage)", "ResultPath": "$.Outputs"}]}, "Transcribe Wait (defaultAudioStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get Transcribe Status (defaultAudioStage)"}, "Get Transcribe Status (defaultAudioStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-CheckTranscribeFunction-89O51Q3AA9L8", "Next": "Did Transcribe Complete (defaultAudioStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Transcribe Failed (defaultAudioStage)", "ResultPath": "$.Outputs"}]}, "Did Transcribe Complete (defaultAudioStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "Transcribe Wait (defaultAudioStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "Transcribe Succeeded (defaultAudioStage)"}], "Default": "Transcribe Failed (defaultAudioStage)"}, "Transcribe Failed (defaultAudioStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Transcribe Succeeded (defaultAudioStage)": {"Type": "Succeed"}}}]}}}',
                'Id': '9c593fe6-87da-4765-918e-35d1f0f7cd5d',
                'Name': 'defaultAudioStage',
                'Next': 'defaultTextStage',
                'Operations': ['Transcribe'],
                'ResourceType': 'STAGE',
                'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
                'Version': 'v0',
                'Status': 'Not Started',
                'Metrics': {},
                'AssetId': 'abcd-1234-efgh',
                'WorkflowExecutionId': botocore.stub.ANY,
                'MetaData': {}
            },
            'defaultPrelimVideoStage': {
                'ApiVersion': '3.0.0',
                'Configuration': {
                    'Mediainfo': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'Thumbnail': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    }
                },
                'Created': '1605822392.5396',
                'Definition': '{"StartAt": "defaultPrelimVideoStage", "States": {"Complete Stage defaultPrelimVideoStage": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G", "End": True}, "defaultPrelimVideoStage": {"Type": "Parallel", "Next": "Complete Stage defaultPrelimVideoStage", "ResultPath": "$.Outputs", "Branches": [{"StartAt": "Filter Thumbnail Media Type? (defaultPrelimVideoStage)", "States": {"Filter Thumbnail Media Type? (defaultPrelimVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Thumbnail", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Thumbnail", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Thumbnail? (defaultPrelimVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Thumbnail Failed (defaultPrelimVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip Thumbnail? (defaultPrelimVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Thumbnail (defaultPrelimVideoStage)"}], "Default": "Thumbnail Not Started (defaultPrelimVideoStage)"}, "Thumbnail Not Started (defaultPrelimVideoStage)": {"Type": "Succeed"}, "Execute Thumbnail (defaultPrelimVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-StartThumbnailFunction-Z3SEQQ2SOMIP", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Thumbnail Wait (defaultPrelimVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Thumbnail Failed (defaultPrelimVideoStage)", "ResultPath": "$.Outputs"}]}, "Thumbnail Wait (defaultPrelimVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get Thumbnail Status (defaultPrelimVideoStage)"}, "Get Thumbnail Status (defaultPrelimVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-CheckThumbnailFunction-1HYU14L5W9F6S", "Next": "Did Thumbnail Complete (defaultPrelimVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Thumbnail Failed (defaultPrelimVideoStage)", "ResultPath": "$.Outputs"}]}, "Did Thumbnail Complete (defaultPrelimVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "Thumbnail Wait (defaultPrelimVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "Thumbnail Succeeded (defaultPrelimVideoStage)"}], "Default": "Thumbnail Failed (defaultPrelimVideoStage)"}, "Thumbnail Failed (defaultPrelimVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Thumbnail Succeeded (defaultPrelimVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter Mediainfo Media Type? (defaultPrelimVideoStage)", "States": {"Filter Mediainfo Media Type? (defaultPrelimVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Mediainfo", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Mediainfo", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Mediainfo? (defaultPrelimVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Mediainfo Failed (defaultPrelimVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip Mediainfo? (defaultPrelimVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Mediainfo (defaultPrelimVideoStage)"}], "Default": "Mediainfo Not Started (defaultPrelimVideoStage)"}, "Mediainfo Not Started (defaultPrelimVideoStage)": {"Type": "Succeed"}, "Execute Mediainfo (defaultPrelimVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-Mediainfo-1DVF30BM43KO", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Did Mediainfo Complete (defaultPrelimVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Mediainfo Failed (defaultPrelimVideoStage)", "ResultPath": "$.Outputs"}]}, "Did Mediainfo Complete (defaultPrelimVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Complete", "Next": "Mediainfo Succeeded (defaultPrelimVideoStage)"}], "Default": "Mediainfo Failed (defaultPrelimVideoStage)"}, "Mediainfo Failed (defaultPrelimVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Mediainfo Succeeded (defaultPrelimVideoStage)": {"Type": "Succeed"}}}]}}}',
                'Id': '9c3d95b9-e266-483c-bd68-a3821cca200f',
                'Name': 'defaultPrelimVideoStage',
                'Next': 'defaultVideoStage',
                'Operations': ['Thumbnail', 'Mediainfo'],
                'ResourceType': 'STAGE',
                'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
                'Version': 'v0',
                'Status': 'Started',
                'Metrics': {},
                'AssetId': 'abcd-1234-efgh',
                'WorkflowExecutionId': botocore.stub.ANY,
                'MetaData': {},
                'Input': {
                    'Media': {
                        'Video': {
                            'S3Bucket': 'testBucket',
                            'S3Key': 'private/assets/abcd-1234-efgh/input/testFile.mp4'
                        }
                    },
                    'MetaData': {}
                }
            },
            'defaultTextStage': {
                'ApiVersion': '3.0.0',
                'Configuration': {
                    'ComprehendEntities': {
                        'Enabled': True,
                        'MediaType': 'Text'
                    },
                    'ComprehendKeyPhrases': {
                        'Enabled': True,
                        'MediaType': 'Text'
                    },
                    'Translate': {
                        'Enabled': True,
                        'MediaType': 'Text',
                        'SourceLanguageCode': 'en',
                        'TargetLanguageCode': 'ru'
                    }
                },
                'Created': '1605822392.521437',
                'Definition': '{"StartAt": "defaultTextStage", "States": {"Complete Stage defaultTextStage": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G", "End": True}, "defaultTextStage": {"Type": "Parallel", "Next": "Complete Stage defaultTextStage", "ResultPath": "$.Outputs", "Branches": [{"StartAt": "Filter Translate Media Type? (defaultTextStage)", "States": {"Filter Translate Media Type? (defaultTextStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Translate", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Translate", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Text", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Translate? (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Translate Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Skip Translate? (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Translate (defaultTextStage)"}], "Default": "Translate Not Started (defaultTextStage)"}, "Translate Not Started (defaultTextStage)": {"Type": "Succeed"}, "Execute Translate (defaultTextStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-TranslateFunction-BQDTYMDCCWBQ", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Did Translate Complete (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Translate Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Did Translate Complete (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Complete", "Next": "Translate Succeeded (defaultTextStage)"}], "Default": "Translate Failed (defaultTextStage)"}, "Translate Failed (defaultTextStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Translate Succeeded (defaultTextStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter ComprehendKeyPhrases Media Type? (defaultTextStage)", "States": {"Filter ComprehendKeyPhrases Media Type? (defaultTextStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "ComprehendKeyPhrases", "Input.$": "$.Input", "Configuration.$": "$.Configuration.ComprehendKeyPhrases", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Text", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip ComprehendKeyPhrases? (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendKeyPhrases Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Skip ComprehendKeyPhrases? (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute ComprehendKeyPhrases (defaultTextStage)"}], "Default": "ComprehendKeyPhrases Not Started (defaultTextStage)"}, "ComprehendKeyPhrases Not Started (defaultTextStage)": {"Type": "Succeed"}, "Execute ComprehendKeyPhrases (defaultTextStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-startKeyPhrases-HBO46ZS9TUR2", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "ComprehendKeyPhrases Wait (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendKeyPhrases Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "ComprehendKeyPhrases Wait (defaultTextStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get ComprehendKeyPhrases Status (defaultTextStage)"}, "Get ComprehendKeyPhrases Status (defaultTextStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-getKeyPhrases-142K58QL4DLFH", "Next": "Did ComprehendKeyPhrases Complete (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendKeyPhrases Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Did ComprehendKeyPhrases Complete (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "ComprehendKeyPhrases Wait (defaultTextStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "ComprehendKeyPhrases Succeeded (defaultTextStage)"}], "Default": "ComprehendKeyPhrases Failed (defaultTextStage)"}, "ComprehendKeyPhrases Failed (defaultTextStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "ComprehendKeyPhrases Succeeded (defaultTextStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter ComprehendEntities Media Type? (defaultTextStage)", "States": {"Filter ComprehendEntities Media Type? (defaultTextStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "ComprehendEntities", "Input.$": "$.Input", "Configuration.$": "$.Configuration.ComprehendEntities", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Text", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip ComprehendEntities? (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendEntities Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Skip ComprehendEntities? (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute ComprehendEntities (defaultTextStage)"}], "Default": "ComprehendEntities Not Started (defaultTextStage)"}, "ComprehendEntities Not Started (defaultTextStage)": {"Type": "Succeed"}, "Execute ComprehendEntities (defaultTextStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQ-startEntityDetection-1JLL7TLKMEPLQ", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "ComprehendEntities Wait (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendEntities Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "ComprehendEntities Wait (defaultTextStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get ComprehendEntities Status (defaultTextStage)"}, "Get ComprehendEntities Status (defaultTextStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-getEntityDetection-AU3SRAKKGKR1", "Next": "Did ComprehendEntities Complete (defaultTextStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ComprehendEntities Failed (defaultTextStage)", "ResultPath": "$.Outputs"}]}, "Did ComprehendEntities Complete (defaultTextStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "ComprehendEntities Wait (defaultTextStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "ComprehendEntities Succeeded (defaultTextStage)"}], "Default": "ComprehendEntities Failed (defaultTextStage)"}, "ComprehendEntities Failed (defaultTextStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "ComprehendEntities Succeeded (defaultTextStage)": {"Type": "Succeed"}}}]}}}',
                'Id': '7ce14df6-6691-4333-8108-951c6ce2f588',
                'Name': 'defaultTextStage',
                'Next': 'defaultTextSynthesisStage',
                'Operations': ['Translate', 'ComprehendKeyPhrases', 'ComprehendEntities'],
                'ResourceType': 'STAGE',
                'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
                'Version': 'v0',
                'Status': 'Not Started',
                'Metrics': {},
                'AssetId': 'abcd-1234-efgh',
                'WorkflowExecutionId': botocore.stub.ANY,
                'MetaData': {}
            },
            'defaultTextSynthesisStage': {
                'ApiVersion': '3.0.0',
                'Configuration': {
                    'Polly': {
                        'Enabled': True,
                        'MediaType': 'Text'
                    }
                },
                'Created': '1605822392.29234',
                'Definition': '{"StartAt": "defaultTextSynthesisStage", "States": {"Complete Stage defaultTextSynthesisStage": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G", "End": True}, "defaultTextSynthesisStage": {"Type": "Parallel", "Next": "Complete Stage defaultTextSynthesisStage", "ResultPath": "$.Outputs", "Branches": [{"StartAt": "Filter Polly Media Type? (defaultTextSynthesisStage)", "States": {"Filter Polly Media Type? (defaultTextSynthesisStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Polly", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Polly", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Text", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Polly? (defaultTextSynthesisStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Polly Failed (defaultTextSynthesisStage)", "ResultPath": "$.Outputs"}]}, "Skip Polly? (defaultTextSynthesisStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Polly (defaultTextSynthesisStage)"}], "Default": "Polly Not Started (defaultTextSynthesisStage)"}, "Polly Not Started (defaultTextSynthesisStage)": {"Type": "Succeed"}, "Execute Polly (defaultTextSynthesisStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-StartPollyFunction-KMVDA4PPE90D", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Polly Wait (defaultTextSynthesisStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Polly Failed (defaultTextSynthesisStage)", "ResultPath": "$.Outputs"}]}, "Polly Wait (defaultTextSynthesisStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get Polly Status (defaultTextSynthesisStage)"}, "Get Polly Status (defaultTextSynthesisStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-CheckPollyFunction-1MCR9QKJ9SQ11", "Next": "Did Polly Complete (defaultTextSynthesisStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Polly Failed (defaultTextSynthesisStage)", "ResultPath": "$.Outputs"}]}, "Did Polly Complete (defaultTextSynthesisStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "Polly Wait (defaultTextSynthesisStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "Polly Succeeded (defaultTextSynthesisStage)"}], "Default": "Polly Failed (defaultTextSynthesisStage)"}, "Polly Failed (defaultTextSynthesisStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Polly Succeeded (defaultTextSynthesisStage)": {"Type": "Succeed"}}}]}}}',
                'End': True,
                'Id': '9d5fcb7d-d8aa-4583-ba88-2f7e01c7f662',
                'Name': 'defaultTextSynthesisStage',
                'Operations': ['Polly'],
                'ResourceType': 'STAGE',
                'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
                'Version': 'v0',
                'Status': 'Not Started',
                'Metrics': {},
                'AssetId': 'abcd-1234-efgh',
                'WorkflowExecutionId': botocore.stub.ANY,
                'MetaData': {}
            },
            'defaultVideoStage': {
                'ApiVersion': '3.0.0',
                'Configuration': {
                    'celebrityRecognition': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'contentModeration': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'faceDetection': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'faceSearch': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'GenericDataLookup': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'labelDetection': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'Mediaconvert': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'personTracking': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'shotDetection': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'technicalCueDetection': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    },
                    'textDetection': {
                        'Enabled': True,
                        'MediaType': 'Video'
                    }
                },
                'Created': '1605822393.258908',
                'Definition': '{"StartAt": "defaultVideoStage", "States": {"Complete Stage defaultVideoStage": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G", "End": True}, "defaultVideoStage": {"Type": "Parallel", "Next": "Complete Stage defaultVideoStage", "ResultPath": "$.Outputs", "Branches": [{"StartAt": "Filter GenericDataLookup Media Type? (defaultVideoStage)", "States": {"Filter GenericDataLookup Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "GenericDataLookup", "Input.$": "$.Input", "Configuration.$": "$.Configuration.GenericDataLookup", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip GenericDataLookup? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "GenericDataLookup Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip GenericDataLookup? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute GenericDataLookup (defaultVideoStage)"}], "Default": "GenericDataLookup Not Started (defaultVideoStage)"}, "GenericDataLookup Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute GenericDataLookup (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-startGenericDataLookup-13CEX0QWQY9J7", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Did GenericDataLookup Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "GenericDataLookup Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did GenericDataLookup Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Complete", "Next": "GenericDataLookup Succeeded (defaultVideoStage)"}], "Default": "GenericDataLookup Failed (defaultVideoStage)"}, "GenericDataLookup Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "GenericDataLookup Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter celebrityRecognition Media Type? (defaultVideoStage)", "States": {"Filter celebrityRecognition Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "celebrityRecognition", "Input.$": "$.Input", "Configuration.$": "$.Configuration.celebrityRecognition", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip celebrityRecognition? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "celebrityRecognition Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip celebrityRecognition? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute celebrityRecognition (defaultVideoStage)"}], "Default": "celebrityRecognition Not Started (defaultVideoStage)"}, "celebrityRecognition Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute celebrityRecognition (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startCelebrityRecognitio-1D14BTFUME8KK", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "celebrityRecognition Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "celebrityRecognition Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "celebrityRecognition Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get celebrityRecognition Status (defaultVideoStage)"}, "Get celebrityRecognition Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkCelebrityRecognitio-CNFP2WPPNNTY", "Next": "Did celebrityRecognition Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "celebrityRecognition Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did celebrityRecognition Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "celebrityRecognition Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "celebrityRecognition Succeeded (defaultVideoStage)"}], "Default": "celebrityRecognition Failed (defaultVideoStage)"}, "celebrityRecognition Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "celebrityRecognition Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter contentModeration Media Type? (defaultVideoStage)", "States": {"Filter contentModeration Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "contentModeration", "Input.$": "$.Input", "Configuration.$": "$.Configuration.contentModeration", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip contentModeration? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "contentModeration Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip contentModeration? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute contentModeration (defaultVideoStage)"}], "Default": "contentModeration Not Started (defaultVideoStage)"}, "contentModeration Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute contentModeration (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-startContentModeration-1SOB9NPL9OU21", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "contentModeration Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "contentModeration Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "contentModeration Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get contentModeration Status (defaultVideoStage)"}, "Get contentModeration Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-checkContentModeration-1WQMPJWYG335Y", "Next": "Did contentModeration Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "contentModeration Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did contentModeration Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "contentModeration Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "contentModeration Succeeded (defaultVideoStage)"}], "Default": "contentModeration Failed (defaultVideoStage)"}, "contentModeration Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "contentModeration Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter faceDetection Media Type? (defaultVideoStage)", "States": {"Filter faceDetection Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "faceDetection", "Input.$": "$.Input", "Configuration.$": "$.Configuration.faceDetection", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip faceDetection? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip faceDetection? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute faceDetection (defaultVideoStage)"}], "Default": "faceDetection Not Started (defaultVideoStage)"}, "faceDetection Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute faceDetection (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startFaceDetection-4YGNSMCBZRVE", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "faceDetection Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "faceDetection Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get faceDetection Status (defaultVideoStage)"}, "Get faceDetection Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkFaceDetection-1GYB309627Y2H", "Next": "Did faceDetection Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did faceDetection Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "faceDetection Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "faceDetection Succeeded (defaultVideoStage)"}], "Default": "faceDetection Failed (defaultVideoStage)"}, "faceDetection Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "faceDetection Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter faceSearch Media Type? (defaultVideoStage)", "States": {"Filter faceSearch Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "faceSearch", "Input.$": "$.Input", "Configuration.$": "$.Configuration.faceSearch", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip faceSearch? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceSearch Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip faceSearch? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute faceSearch (defaultVideoStage)"}], "Default": "faceSearch Not Started (defaultVideoStage)"}, "faceSearch Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute faceSearch (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-startFaceSearch-1IZHRQVB9NZL6", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "faceSearch Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceSearch Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "faceSearch Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get faceSearch Status (defaultVideoStage)"}, "Get faceSearch Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-checkFaceSearch-ZQN9SPW3H754", "Next": "Did faceSearch Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "faceSearch Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did faceSearch Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "faceSearch Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "faceSearch Succeeded (defaultVideoStage)"}], "Default": "faceSearch Failed (defaultVideoStage)"}, "faceSearch Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "faceSearch Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter labelDetection Media Type? (defaultVideoStage)", "States": {"Filter labelDetection Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "labelDetection", "Input.$": "$.Input", "Configuration.$": "$.Configuration.labelDetection", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip labelDetection? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "labelDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip labelDetection? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute labelDetection (defaultVideoStage)"}], "Default": "labelDetection Not Started (defaultVideoStage)"}, "labelDetection Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute labelDetection (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startLabelDetection-125TMWFXWCDUW", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "labelDetection Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "labelDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "labelDetection Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get labelDetection Status (defaultVideoStage)"}, "Get labelDetection Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkLabelDetection-1TJTKK0SC9ABR", "Next": "Did labelDetection Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "labelDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did labelDetection Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "labelDetection Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "labelDetection Succeeded (defaultVideoStage)"}], "Default": "labelDetection Failed (defaultVideoStage)"}, "labelDetection Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "labelDetection Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter personTracking Media Type? (defaultVideoStage)", "States": {"Filter personTracking Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "personTracking", "Input.$": "$.Input", "Configuration.$": "$.Configuration.personTracking", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip personTracking? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "personTracking Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip personTracking? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute personTracking (defaultVideoStage)"}], "Default": "personTracking Not Started (defaultVideoStage)"}, "personTracking Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute personTracking (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startPersonTracking-113JL6LE8X356", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "personTracking Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "personTracking Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "personTracking Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get personTracking Status (defaultVideoStage)"}, "Get personTracking Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkPersonTracking-1HD4C4PV511CU", "Next": "Did personTracking Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "personTracking Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did personTracking Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "personTracking Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "personTracking Succeeded (defaultVideoStage)"}], "Default": "personTracking Failed (defaultVideoStage)"}, "personTracking Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "personTracking Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter textDetection Media Type? (defaultVideoStage)", "States": {"Filter textDetection Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "textDetection", "Input.$": "$.Input", "Configuration.$": "$.Configuration.textDetection", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip textDetection? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "textDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip textDetection? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute textDetection (defaultVideoStage)"}], "Default": "textDetection Not Started (defaultVideoStage)"}, "textDetection Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute textDetection (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startTextDetection-1VKG25EE66L1I", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "textDetection Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "textDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "textDetection Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get textDetection Status (defaultVideoStage)"}, "Get textDetection Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkTextDetection-1I7WEG7QGZLS0", "Next": "Did textDetection Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "textDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did textDetection Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "textDetection Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "textDetection Succeeded (defaultVideoStage)"}], "Default": "textDetection Failed (defaultVideoStage)"}, "textDetection Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "textDetection Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter Mediaconvert Media Type? (defaultVideoStage)", "States": {"Filter Mediaconvert Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "Mediaconvert", "Input.$": "$.Input", "Configuration.$": "$.Configuration.Mediaconvert", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip Mediaconvert? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Mediaconvert Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip Mediaconvert? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute Mediaconvert (defaultVideoStage)"}], "Default": "Mediaconvert Not Started (defaultVideoStage)"}, "Mediaconvert Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute Mediaconvert (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-StartMediaConvertFunctio-X0UUOJVL6AX2", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Mediaconvert Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Mediaconvert Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Mediaconvert Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get Mediaconvert Status (defaultVideoStage)"}, "Get Mediaconvert Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-CheckMediaConvertFunctio-1W0HFF4G4AYSD", "Next": "Did Mediaconvert Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Mediaconvert Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did Mediaconvert Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "Mediaconvert Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "Mediaconvert Succeeded (defaultVideoStage)"}], "Default": "Mediaconvert Failed (defaultVideoStage)"}, "Mediaconvert Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "Mediaconvert Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter technicalCueDetection Media Type? (defaultVideoStage)", "States": {"Filter technicalCueDetection Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "technicalCueDetection", "Input.$": "$.Input", "Configuration.$": "$.Configuration.technicalCueDetection", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip technicalCueDetection? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "technicalCueDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip technicalCueDetection? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute technicalCueDetection (defaultVideoStage)"}], "Default": "technicalCueDetection Not Started (defaultVideoStage)"}, "technicalCueDetection Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute technicalCueDetection (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startTechnicalCueDetecti-1NWCRDJLZP5LV", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "technicalCueDetection Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "technicalCueDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "technicalCueDetection Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get technicalCueDetection Status (defaultVideoStage)"}, "Get technicalCueDetection Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkTechnicalCueDetecti-QY16N45OC9SS", "Next": "Did technicalCueDetection Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "technicalCueDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did technicalCueDetection Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "technicalCueDetection Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "technicalCueDetection Succeeded (defaultVideoStage)"}], "Default": "technicalCueDetection Failed (defaultVideoStage)"}, "technicalCueDetection Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "technicalCueDetection Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}, {"StartAt": "Filter shotDetection Media Type? (defaultVideoStage)", "States": {"Filter shotDetection Media Type? (defaultVideoStage)": {"Type": "Task", "Parameters": {"StageName.$": "$.Name", "Name": "shotDetection", "Input.$": "$.Input", "Configuration.$": "$.Configuration.shotDetection", "AssetId.$": "$.AssetId", "WorkflowExecutionId.$": "$.WorkflowExecutionId", "Type": "Video", "Status": "$.Status"}, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "Skip shotDetection? (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "shotDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Skip shotDetection? (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Started", "Next": "Execute shotDetection (defaultVideoStage)"}], "Default": "shotDetection Not Started (defaultVideoStage)"}, "shotDetection Not Started (defaultVideoStage)": {"Type": "Succeed"}, "Execute shotDetection (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startShotDetection-1Q2DLD30UC91V", "ResultPath": "$.Outputs", "OutputPath": "$.Outputs", "Next": "shotDetection Wait (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "shotDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "shotDetection Wait (defaultVideoStage)": {"Type": "Wait", "Seconds": 10, "Next": "Get shotDetection Status (defaultVideoStage)"}, "Get shotDetection Status (defaultVideoStage)": {"Type": "Task", "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkShotDetection-18OOGE8QDQO2W", "Next": "Did shotDetection Complete (defaultVideoStage)", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}], "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "shotDetection Failed (defaultVideoStage)", "ResultPath": "$.Outputs"}]}, "Did shotDetection Complete (defaultVideoStage)": {"Type": "Choice", "Choices": [{"Variable": "$.Status", "StringEquals": "Executing", "Next": "shotDetection Wait (defaultVideoStage)"}, {"Variable": "$.Status", "StringEquals": "Complete", "Next": "shotDetection Succeeded (defaultVideoStage)"}], "Default": "shotDetection Failed (defaultVideoStage)"}, "shotDetection Failed (defaultVideoStage)": {"Type": "Task", "End": True, "Resource": "arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9", "ResultPath": "$", "Retry": [{"ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2}]}, "shotDetection Succeeded (defaultVideoStage)": {"Type": "Succeed"}}}]}}}',
                'Id': 'dca4038a-7ac7-41e9-8044-76bed36d2c9f',
                'Name': 'defaultVideoStage',
                'Next': 'defaultAudioStage',
                'Operations': ['GenericDataLookup', 'celebrityRecognition', 'contentModeration', 'faceDetection',
                               'faceSearch', 'labelDetection', 'personTracking', 'textDetection', 'Mediaconvert',
                               'technicalCueDetection', 'shotDetection'],
                'ResourceType': 'STAGE',
                'ServiceToken': 'arn:aws:lambda:us-west-2:123456789:function:mie-MediaInsightsWorkflowAp-WorkflowCustomResource-1234ABCD',
                'Version': 'v0',
                'Status': 'Not Started',
                'Metrics': {},
                'AssetId': 'abcd-1234-efgh',
                'WorkflowExecutionId': botocore.stub.ANY,
                'MetaData': {}
            }
        },
        'StaleOperations': [],
        'StaleStages': [],
        'StartAt': 'defaultPrelimVideoStage',
        'StateMachineArn': 'arn:aws:states:us-west-2:123456789:stateMachine:CasVideoWorkflow-aqx5d8',
        'Trigger': 'custom-resource',
        'Version': 'v0'
    },
    'Status': 'Queued'
}

sample_workflow_status_by_asset_id = [{
    "CurrentStage": {"S": "End"},
    "Workflow": {"M":
                     {"Name": {"S": "TestingWF"}}
                 },
    "Status": {"S": "Complete"},
    "Id": {"S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"},
    "AssetId": {"S": "c1752400-ba2f-4682-a8dd-6eba0932d148"},
    "Created": {"S": "1605223694.691767"},
    "StateMachineExecutionArn": {"S": "arn:aws:xxxx"}
}]

sample_workflow_status_by_id = {
    "Configuration": {
        "M": {

        }
    },
    "Status": {
        "S": "Complete"
    },
    "ResourceType": {
        "S": "WORKFLOW_EXECUTION"
    },
    "Created": {
        "S": "1605223694.691767"
    },
    "StateMachineExecutionArn": {
        "S": "arn:aws:states:us-west-2:123456789:execution:TestingWF-aqx5d8:TestingWF0c6c202a-dd21-4791-b7b1-28c0ab60575d"
    },
    "CurrentStage": {
        "S": "End"
    },
    "Version": {
        "S": "v0"
    },
    "Trigger": {
        "S": "api"
    },
    "Workflow": {
        "M": {
            "ApiVersion": {
                "S": "3.0.0"
            },
            "Created": {
                "S": "1605223691.751675"
            },
            "Id": {
                "S": "685cf548-14d7-4496-b96c-6508db93883e"
            },
            "Name": {
                "S": "TestingWF"
            },
            "Operations": {
                "L": [{
                        "S": "Mediainfo"
                    },
                    {
                        "S": "Thumbnail"
                    },
                    {
                        "S": "celebrityRecognition"
                    },
                    {
                        "S": "contentModeration"
                    },
                    {
                        "S": "faceDetection"
                    },
                    {
                        "S": "labelDetection"
                    },
                    {
                        "S": "personTracking"
                    },
                    {
                        "S": "shotDetection"
                    },
                    {
                        "S": "textDetection"
                    },
                    {
                        "S": "Mediaconvert"
                    },
                    {
                        "S": "technicalCueDetection"
                    },
                    {
                        "S": "Transcribe"
                    },
                    {
                        "S": "Translate"
                    },
                    {
                        "S": "ComprehendKeyPhrases"
                    },
                    {
                        "S": "ComprehendEntities"
                    }
                ]
            },
            "ResourceType": {
                "S": "WORKFLOW"
            },
            "Revisions": {
                "S": "1"
            },
            "Stages": {
                "M": {
                    "TestAudio": {
                        "M": {
                            "Status": {
                                "S": "Complete"
                            },
                            "ApiVersion": {
                                "S": "3.0.0"
                            },
                            "Configuration": {
                                "M": {
                                    "Transcribe": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Audio"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            },
                                            "TranscribeLanguage": {
                                                "S": "en-US"
                                            }
                                        }
                                    }
                                }
                            },
                            "WorkflowExecutionId": {
                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                            },
                            "Definition": {
                                "S": "{\"StartAt\": \"TestAudio\", \"States\": {\"Complete Stage TestAudio\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"TestAudio\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage TestAudio\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Transcribe Media Type? (TestAudio)\", \"States\": {\"Filter Transcribe Media Type? (TestAudio)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Transcribe\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Transcribe\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Audio\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Transcribe? (TestAudio)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (TestAudio)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Transcribe? (TestAudio)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Transcribe (TestAudio)\"}], \"Default\": \"Transcribe Not Started (TestAudio)\"}, \"Transcribe Not Started (TestAudio)\": {\"Type\": \"Succeed\"}, \"Execute Transcribe (TestAudio)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-StartTranscribeFunction-153XYIT0IY722\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Transcribe Wait (TestAudio)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (TestAudio)\", \"ResultPath\": \"$.Outputs\"}]}, \"Transcribe Wait (TestAudio)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Transcribe Status (TestAudio)\"}, \"Get Transcribe Status (TestAudio)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y-CheckTranscribeFunction-89O51Q3AA9L8\", \"Next\": \"Did Transcribe Complete (TestAudio)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Transcribe Failed (TestAudio)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Transcribe Complete (TestAudio)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Transcribe Wait (TestAudio)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Transcribe Succeeded (TestAudio)\"}], \"Default\": \"Transcribe Failed (TestAudio)\"}, \"Transcribe Failed (TestAudio)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Transcribe Succeeded (TestAudio)\": {\"Type\": \"Succeed\"}}}]}}}"
                            },
                            "ResourceType": {
                                "S": "STAGE"
                            },
                            "Name": {
                                "S": "TestAudio"
                            },
                            "Created": {
                                "S": "1605223690.793251"
                            },
                            "Metrics": {
                                "M": {

                                }
                            },
                            "Input": {
                                "M": {
                                    "Media": {
                                        "M": {
                                            "Thumbnail": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                    }
                                                }
                                            },
                                            "Audio": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                    }
                                                }
                                            },
                                            "Video": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            },
                                            "ProxyEncode": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "MetaData": {
                                        "M": {
                                            "MediaconvertJobId": {
                                                "S": "1605223714672-o0nmx4"
                                            },
                                            "Mediainfo_num_audio_tracks": {
                                                "S": "1"
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "JobId": {
                                                "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                            },
                                            "MediaconvertInputFile": {
                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                            }
                                        }
                                    }
                                }
                            },
                            "Version": {
                                "S": "v0"
                            },
                            "MetaData": {
                                "M": {

                                }
                            },
                            "Next": {
                                "S": "TestText"
                            },
                            "Outputs": {
                                "L": [{
                                    "M": {
                                        "Status": {
                                            "S": "Complete"
                                        },
                                        "Input": {
                                            "M": {
                                                "Media": {
                                                    "M": {
                                                        "Thumbnail": {
                                                            "M": {
                                                                "S3Bucket": {
                                                                    "S": "mie-dataplane-1s54zv3jhht0m"
                                                                },
                                                                "S3Key": {
                                                                    "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                                }
                                                            }
                                                        },
                                                        "Audio": {
                                                            "M": {
                                                                "S3Bucket": {
                                                                    "S": "mie-dataplane-1s54zv3jhht0m"
                                                                },
                                                                "S3Key": {
                                                                    "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                                }
                                                            }
                                                        },
                                                        "Video": {
                                                            "M": {
                                                                "S3Bucket": {
                                                                    "S": "mie-dataplane-1s54zv3jhht0m"
                                                                },
                                                                "S3Key": {
                                                                    "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                }
                                                            }
                                                        },
                                                        "ProxyEncode": {
                                                            "M": {
                                                                "S3Bucket": {
                                                                    "S": "mie-dataplane-1s54zv3jhht0m"
                                                                },
                                                                "S3Key": {
                                                                    "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                                }
                                                            }
                                                        }
                                                    }
                                                },
                                                "MetaData": {
                                                    "M": {
                                                        "MediaconvertJobId": {
                                                            "S": "1605223714672-o0nmx4"
                                                        },
                                                        "Mediainfo_num_audio_tracks": {
                                                            "S": "1"
                                                        },
                                                        "AssetId": {
                                                            "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                        },
                                                        "WorkflowExecutionId": {
                                                            "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                        },
                                                        "JobId": {
                                                            "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                                        },
                                                        "MediaconvertInputFile": {
                                                            "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "Configuration": {
                                            "M": {
                                                "MediaType": {
                                                    "S": "Audio"
                                                },
                                                "Enabled": {
                                                    "BOOL": True
                                                },
                                                "TranscribeLanguage": {
                                                    "S": "en-US"
                                                }
                                            }
                                        },
                                        "WorkflowExecutionId": {
                                            "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                        },
                                        "MetaData": {
                                            "M": {
                                                "TranscribeJobId": {
                                                    "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                },
                                                "AssetId": {
                                                    "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                },
                                                "WorkflowExecutionId": {
                                                    "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                }
                                            }
                                        },
                                        "Media": {
                                            "M": {
                                                "Text": {
                                                    "M": {
                                                        "S3Bucket": {
                                                            "S": "mie-dataplane-1s54zv3jhht0m"
                                                        },
                                                        "S3Key": {
                                                            "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Transcribe.json"
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "AssetId": {
                                            "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                        },
                                        "Name": {
                                            "S": "Transcribe"
                                        }
                                    }
                                }]
                            },
                            "Id": {
                                "S": "027b0382-88ba-4a3e-9e77-c9d14e41b0cc"
                            },
                            "Operations": {
                                "L": [{
                                    "S": "Transcribe"
                                }]
                            },
                            "AssetId": {
                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                            }
                        }
                    },
                    "TestPreprocess": {
                        "M": {
                            "Status": {
                                "S": "Complete"
                            },
                            "ApiVersion": {
                                "S": "3.0.0"
                            },
                            "Configuration": {
                                "M": {
                                    "Thumbnail": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "Mediainfo": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    }
                                }
                            },
                            "WorkflowExecutionId": {
                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                            },
                            "Definition": {
                                "S": "{\"StartAt\": \"TestPreprocess\", \"States\": {\"Complete Stage TestPreprocess\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"TestPreprocess\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage TestPreprocess\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Mediainfo Media Type? (TestPreprocess)\", \"States\": {\"Filter Mediainfo Media Type? (TestPreprocess)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Mediainfo\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Mediainfo\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Mediainfo? (TestPreprocess)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediainfo Failed (TestPreprocess)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Mediainfo? (TestPreprocess)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Mediainfo (TestPreprocess)\"}], \"Default\": \"Mediainfo Not Started (TestPreprocess)\"}, \"Mediainfo Not Started (TestPreprocess)\": {\"Type\": \"Succeed\"}, \"Execute Mediainfo (TestPreprocess)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-Mediainfo-1DVF30BM43KO\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Did Mediainfo Complete (TestPreprocess)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediainfo Failed (TestPreprocess)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Mediainfo Complete (TestPreprocess)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Mediainfo Succeeded (TestPreprocess)\"}], \"Default\": \"Mediainfo Failed (TestPreprocess)\"}, \"Mediainfo Failed (TestPreprocess)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Mediainfo Succeeded (TestPreprocess)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter Thumbnail Media Type? (TestPreprocess)\", \"States\": {\"Filter Thumbnail Media Type? (TestPreprocess)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Thumbnail\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Thumbnail\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Thumbnail? (TestPreprocess)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (TestPreprocess)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Thumbnail? (TestPreprocess)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Thumbnail (TestPreprocess)\"}], \"Default\": \"Thumbnail Not Started (TestPreprocess)\"}, \"Thumbnail Not Started (TestPreprocess)\": {\"Type\": \"Succeed\"}, \"Execute Thumbnail (TestPreprocess)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-StartThumbnailFunction-Z3SEQQ2SOMIP\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Thumbnail Wait (TestPreprocess)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (TestPreprocess)\", \"ResultPath\": \"$.Outputs\"}]}, \"Thumbnail Wait (TestPreprocess)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Thumbnail Status (TestPreprocess)\"}, \"Get Thumbnail Status (TestPreprocess)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-CheckThumbnailFunction-1HYU14L5W9F6S\", \"Next\": \"Did Thumbnail Complete (TestPreprocess)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Thumbnail Failed (TestPreprocess)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Thumbnail Complete (TestPreprocess)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Thumbnail Wait (TestPreprocess)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Thumbnail Succeeded (TestPreprocess)\"}], \"Default\": \"Thumbnail Failed (TestPreprocess)\"}, \"Thumbnail Failed (TestPreprocess)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Thumbnail Succeeded (TestPreprocess)\": {\"Type\": \"Succeed\"}}}]}}}"
                            },
                            "ResourceType": {
                                "S": "STAGE"
                            },
                            "Name": {
                                "S": "TestPreprocess"
                            },
                            "Created": {
                                "S": "1605223689.292053"
                            },
                            "Metrics": {
                                "M": {

                                }
                            },
                            "Input": {
                                "M": {
                                    "Media": {
                                        "M": {
                                            "Video": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "MetaData": {
                                        "M": {

                                        }
                                    }
                                }
                            },
                            "Version": {
                                "S": "v0"
                            },
                            "MetaData": {
                                "M": {

                                }
                            },
                            "Next": {
                                "S": "TestVideo"
                            },
                            "Outputs": {
                                "L": [{
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {

                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Video"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "Mediainfo_num_audio_tracks": {
                                                        "S": "1"
                                                    },
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "Mediainfo"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {

                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Video"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "MediaconvertJobId": {
                                                        "S": "1605223698695-b3f1vm"
                                                    },
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    },
                                                    "MediaconvertInputFile": {
                                                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            },
                                            "Media": {
                                                "M": {
                                                    "Thumbnail": {
                                                        "M": {
                                                            "S3Bucket": {
                                                                "S": "mie-dataplane-1s54zv3jhht0m"
                                                            },
                                                            "S3Key": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                            }
                                                        }
                                                    },
                                                    "Audio": {
                                                        "M": {
                                                            "S3Bucket": {
                                                                "S": "mie-dataplane-1s54zv3jhht0m"
                                                            },
                                                            "S3Key": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                            }
                                                        }
                                                    },
                                                    "ProxyEncode": {
                                                        "M": {
                                                            "S3Bucket": {
                                                                "S": "mie-dataplane-1s54zv3jhht0m"
                                                            },
                                                            "S3Key": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "Thumbnail"
                                            }
                                        }
                                    }
                                ]
                            },
                            "Id": {
                                "S": "69df1ed3-95ae-4d3c-a62b-ef565cf62556"
                            },
                            "Operations": {
                                "L": [{
                                        "S": "Mediainfo"
                                    },
                                    {
                                        "S": "Thumbnail"
                                    }
                                ]
                            },
                            "AssetId": {
                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                            }
                        }
                    },
                    "TestText": {
                        "M": {
                            "Status": {
                                "S": "Complete"
                            },
                            "ApiVersion": {
                                "S": "3.0.0"
                            },
                            "Configuration": {
                                "M": {
                                    "Translate": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Text"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            },
                                            "TargetLanguageCode": {
                                                "S": "ru"
                                            },
                                            "SourceLanguageCode": {
                                                "S": "en"
                                            }
                                        }
                                    },
                                    "ComprehendEntities": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Text"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "ComprehendKeyPhrases": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Text"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    }
                                }
                            },
                            "WorkflowExecutionId": {
                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                            },
                            "Definition": {
                                "S": "{\"StartAt\": \"TestText\", \"States\": {\"Complete Stage TestText\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"TestText\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage TestText\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter Translate Media Type? (TestText)\", \"States\": {\"Filter Translate Media Type? (TestText)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Translate\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Translate\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Translate? (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Translate Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Translate? (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Translate (TestText)\"}], \"Default\": \"Translate Not Started (TestText)\"}, \"Translate Not Started (TestText)\": {\"Type\": \"Succeed\"}, \"Execute Translate (TestText)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-TranslateFunction-BQDTYMDCCWBQ\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Did Translate Complete (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Translate Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Translate Complete (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Translate Succeeded (TestText)\"}], \"Default\": \"Translate Failed (TestText)\"}, \"Translate Failed (TestText)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Translate Succeeded (TestText)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter ComprehendKeyPhrases Media Type? (TestText)\", \"States\": {\"Filter ComprehendKeyPhrases Media Type? (TestText)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"ComprehendKeyPhrases\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.ComprehendKeyPhrases\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip ComprehendKeyPhrases? (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip ComprehendKeyPhrases? (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute ComprehendKeyPhrases (TestText)\"}], \"Default\": \"ComprehendKeyPhrases Not Started (TestText)\"}, \"ComprehendKeyPhrases Not Started (TestText)\": {\"Type\": \"Succeed\"}, \"Execute ComprehendKeyPhrases (TestText)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-startKeyPhrases-HBO46ZS9TUR2\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"ComprehendKeyPhrases Wait (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"ComprehendKeyPhrases Wait (TestText)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get ComprehendKeyPhrases Status (TestText)\"}, \"Get ComprehendKeyPhrases Status (TestText)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIUV-getKeyPhrases-142K58QL4DLFH\", \"Next\": \"Did ComprehendKeyPhrases Complete (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendKeyPhrases Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did ComprehendKeyPhrases Complete (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"ComprehendKeyPhrases Wait (TestText)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"ComprehendKeyPhrases Succeeded (TestText)\"}], \"Default\": \"ComprehendKeyPhrases Failed (TestText)\"}, \"ComprehendKeyPhrases Failed (TestText)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"ComprehendKeyPhrases Succeeded (TestText)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter ComprehendEntities Media Type? (TestText)\", \"States\": {\"Filter ComprehendEntities Media Type? (TestText)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"ComprehendEntities\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.ComprehendEntities\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Text\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip ComprehendEntities? (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip ComprehendEntities? (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute ComprehendEntities (TestText)\"}], \"Default\": \"ComprehendEntities Not Started (TestText)\"}, \"ComprehendEntities Not Started (TestText)\": {\"Type\": \"Succeed\"}, \"Execute ComprehendEntities (TestText)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQ-startEntityDetection-1JLL7TLKMEPLQ\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"ComprehendEntities Wait (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"ComprehendEntities Wait (TestText)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get ComprehendEntities Status (TestText)\"}, \"Get ComprehendEntities Status (TestText)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-getEntityDetection-AU3SRAKKGKR1\", \"Next\": \"Did ComprehendEntities Complete (TestText)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"ComprehendEntities Failed (TestText)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did ComprehendEntities Complete (TestText)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"ComprehendEntities Wait (TestText)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"ComprehendEntities Succeeded (TestText)\"}], \"Default\": \"ComprehendEntities Failed (TestText)\"}, \"ComprehendEntities Failed (TestText)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"ComprehendEntities Succeeded (TestText)\": {\"Type\": \"Succeed\"}}}]}}}"
                            },
                            "ResourceType": {
                                "S": "STAGE"
                            },
                            "Name": {
                                "S": "TestText"
                            },
                            "Created": {
                                "S": "1605223691.372269"
                            },
                            "Metrics": {
                                "M": {

                                }
                            },
                            "Input": {
                                "M": {
                                    "Media": {
                                        "M": {
                                            "Text": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Transcribe.json"
                                                    }
                                                }
                                            },
                                            "Thumbnail": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                    }
                                                }
                                            },
                                            "Audio": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                    }
                                                }
                                            },
                                            "Video": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            },
                                            "ProxyEncode": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "MetaData": {
                                        "M": {
                                            "TranscribeJobId": {
                                                "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "Mediainfo_num_audio_tracks": {
                                                "S": "1"
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MediaconvertJobId": {
                                                "S": "1605223714672-o0nmx4"
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "JobId": {
                                                "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                            },
                                            "MediaconvertInputFile": {
                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                            }
                                        }
                                    }
                                }
                            },
                            "Version": {
                                "S": "v0"
                            },
                            "MetaData": {
                                "M": {

                                }
                            },
                            "Outputs": {
                                "L": [{
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Text": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Transcribe.json"
                                                                    }
                                                                }
                                                            },
                                                            "Thumbnail": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                                    }
                                                                }
                                                            },
                                                            "Audio": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "ProxyEncode": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {
                                                            "TranscribeJobId": {
                                                                "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "Mediainfo_num_audio_tracks": {
                                                                "S": "1"
                                                            },
                                                            "WorkflowExecutionId": {
                                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "MediaconvertJobId": {
                                                                "S": "1605223714672-o0nmx4"
                                                            },
                                                            "AssetId": {
                                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                            },
                                                            "JobId": {
                                                                "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                                            },
                                                            "MediaconvertInputFile": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Text"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    },
                                                    "TargetLanguageCode": {
                                                        "S": "ru"
                                                    },
                                                    "SourceLanguageCode": {
                                                        "S": "en"
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {

                                                }
                                            },
                                            "Media": {
                                                "M": {
                                                    "Text": {
                                                        "M": {
                                                            "S3Bucket": {
                                                                "S": "mie-dataplane-1s54zv3jhht0m"
                                                            },
                                                            "S3Key": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Translate.json"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "Translate"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Text": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Transcribe.json"
                                                                    }
                                                                }
                                                            },
                                                            "Thumbnail": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                                    }
                                                                }
                                                            },
                                                            "Audio": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "ProxyEncode": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {
                                                            "TranscribeJobId": {
                                                                "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "Mediainfo_num_audio_tracks": {
                                                                "S": "1"
                                                            },
                                                            "WorkflowExecutionId": {
                                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "MediaconvertJobId": {
                                                                "S": "1605223714672-o0nmx4"
                                                            },
                                                            "AssetId": {
                                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                            },
                                                            "JobId": {
                                                                "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                                            },
                                                            "MediaconvertInputFile": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Text"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "output_uri": {
                                                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d//comprehend_phrases/123456789-KP-a349b93aab098876349add3300a49484/output/output.tar.gz"
                                                    },
                                                    "comprehend_entity_job_id": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    },
                                                    "comprehend_phrases_job_id": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "ComprehendKeyPhrases"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Text": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Transcribe.json"
                                                                    }
                                                                }
                                                            },
                                                            "Thumbnail": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                                    }
                                                                }
                                                            },
                                                            "Audio": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "ProxyEncode": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {
                                                            "TranscribeJobId": {
                                                                "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "Mediainfo_num_audio_tracks": {
                                                                "S": "1"
                                                            },
                                                            "WorkflowExecutionId": {
                                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "MediaconvertJobId": {
                                                                "S": "1605223714672-o0nmx4"
                                                            },
                                                            "AssetId": {
                                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                            },
                                                            "JobId": {
                                                                "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                                            },
                                                            "MediaconvertInputFile": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Text"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "comprehend_entity_job_id": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    },
                                                    "output_uri": {
                                                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d//comprehend_entities/123456789-NER-6a65c759a9f2dcf6838ea782de3f95a7/output/output.tar.gz"
                                                    },
                                                    "entity_output_uri": {
                                                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d//comprehend_entities"
                                                    }
                                                }
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "ComprehendEntities"
                                            }
                                        }
                                    }
                                ]
                            },
                            "End": {
                                "BOOL": True
                            },
                            "Id": {
                                "S": "393ccf25-28a6-46e8-b565-5376049e307c"
                            },
                            "Operations": {
                                "L": [{
                                        "S": "Translate"
                                    },
                                    {
                                        "S": "ComprehendKeyPhrases"
                                    },
                                    {
                                        "S": "ComprehendEntities"
                                    }
                                ]
                            },
                            "AssetId": {
                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                            }
                        }
                    },
                    "TestVideo": {
                        "M": {
                            "Status": {
                                "S": "Complete"
                            },
                            "ApiVersion": {
                                "S": "3.0.0"
                            },
                            "Configuration": {
                                "M": {
                                    "faceDetection": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "textDetection": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "celebrityRecognition": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "labelDetection": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "personTracking": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "shotDetection": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "Mediaconvert": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "technicalCueDetection": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    },
                                    "contentModeration": {
                                        "M": {
                                            "MediaType": {
                                                "S": "Video"
                                            },
                                            "Enabled": {
                                                "BOOL": True
                                            }
                                        }
                                    }
                                }
                            },
                            "WorkflowExecutionId": {
                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                            },
                            "Definition": {
                                "S": "{\"StartAt\": \"TestVideo\", \"States\": {\"Complete Stage TestVideo\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-CompleteStageLambda-179N7ETJ0L46G\", \"End\": True}, \"TestVideo\": {\"Type\": \"Parallel\", \"Next\": \"Complete Stage TestVideo\", \"ResultPath\": \"$.Outputs\", \"Branches\": [{\"StartAt\": \"Filter celebrityRecognition Media Type? (TestVideo)\", \"States\": {\"Filter celebrityRecognition Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"celebrityRecognition\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.celebrityRecognition\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip celebrityRecognition? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip celebrityRecognition? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute celebrityRecognition (TestVideo)\"}], \"Default\": \"celebrityRecognition Not Started (TestVideo)\"}, \"celebrityRecognition Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute celebrityRecognition (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startCelebrityRecognitio-1D14BTFUME8KK\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"celebrityRecognition Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"celebrityRecognition Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get celebrityRecognition Status (TestVideo)\"}, \"Get celebrityRecognition Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkCelebrityRecognitio-CNFP2WPPNNTY\", \"Next\": \"Did celebrityRecognition Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"celebrityRecognition Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did celebrityRecognition Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"celebrityRecognition Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"celebrityRecognition Succeeded (TestVideo)\"}], \"Default\": \"celebrityRecognition Failed (TestVideo)\"}, \"celebrityRecognition Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"celebrityRecognition Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter contentModeration Media Type? (TestVideo)\", \"States\": {\"Filter contentModeration Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"contentModeration\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.contentModeration\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip contentModeration? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip contentModeration? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute contentModeration (TestVideo)\"}], \"Default\": \"contentModeration Not Started (TestVideo)\"}, \"contentModeration Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute contentModeration (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-startContentModeration-1SOB9NPL9OU21\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"contentModeration Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"contentModeration Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get contentModeration Status (TestVideo)\"}, \"Get contentModeration Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5-checkContentModeration-1WQMPJWYG335Y\", \"Next\": \"Did contentModeration Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"contentModeration Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did contentModeration Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"contentModeration Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"contentModeration Succeeded (TestVideo)\"}], \"Default\": \"contentModeration Failed (TestVideo)\"}, \"contentModeration Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"contentModeration Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter faceDetection Media Type? (TestVideo)\", \"States\": {\"Filter faceDetection Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"faceDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.faceDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip faceDetection? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip faceDetection? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute faceDetection (TestVideo)\"}], \"Default\": \"faceDetection Not Started (TestVideo)\"}, \"faceDetection Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute faceDetection (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startFaceDetection-4YGNSMCBZRVE\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"faceDetection Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"faceDetection Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get faceDetection Status (TestVideo)\"}, \"Get faceDetection Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkFaceDetection-1GYB309627Y2H\", \"Next\": \"Did faceDetection Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"faceDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did faceDetection Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"faceDetection Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"faceDetection Succeeded (TestVideo)\"}], \"Default\": \"faceDetection Failed (TestVideo)\"}, \"faceDetection Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"faceDetection Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter labelDetection Media Type? (TestVideo)\", \"States\": {\"Filter labelDetection Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"labelDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.labelDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip labelDetection? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip labelDetection? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute labelDetection (TestVideo)\"}], \"Default\": \"labelDetection Not Started (TestVideo)\"}, \"labelDetection Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute labelDetection (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startLabelDetection-125TMWFXWCDUW\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"labelDetection Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"labelDetection Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get labelDetection Status (TestVideo)\"}, \"Get labelDetection Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkLabelDetection-1TJTKK0SC9ABR\", \"Next\": \"Did labelDetection Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"labelDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did labelDetection Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"labelDetection Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"labelDetection Succeeded (TestVideo)\"}], \"Default\": \"labelDetection Failed (TestVideo)\"}, \"labelDetection Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"labelDetection Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter personTracking Media Type? (TestVideo)\", \"States\": {\"Filter personTracking Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"personTracking\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.personTracking\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip personTracking? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip personTracking? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute personTracking (TestVideo)\"}], \"Default\": \"personTracking Not Started (TestVideo)\"}, \"personTracking Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute personTracking (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-startPersonTracking-113JL6LE8X356\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"personTracking Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"personTracking Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get personTracking Status (TestVideo)\"}, \"Get personTracking Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQI-checkPersonTracking-1HD4C4PV511CU\", \"Next\": \"Did personTracking Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"personTracking Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did personTracking Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"personTracking Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"personTracking Succeeded (TestVideo)\"}], \"Default\": \"personTracking Failed (TestVideo)\"}, \"personTracking Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"personTracking Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter shotDetection Media Type? (TestVideo)\", \"States\": {\"Filter shotDetection Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"shotDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.shotDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip shotDetection? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip shotDetection? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute shotDetection (TestVideo)\"}], \"Default\": \"shotDetection Not Started (TestVideo)\"}, \"shotDetection Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute shotDetection (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startShotDetection-1Q2DLD30UC91V\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"shotDetection Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"shotDetection Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get shotDetection Status (TestVideo)\"}, \"Get shotDetection Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkShotDetection-18OOGE8QDQO2W\", \"Next\": \"Did shotDetection Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"shotDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did shotDetection Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"shotDetection Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"shotDetection Succeeded (TestVideo)\"}], \"Default\": \"shotDetection Failed (TestVideo)\"}, \"shotDetection Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"shotDetection Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter textDetection Media Type? (TestVideo)\", \"States\": {\"Filter textDetection Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"textDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.textDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip textDetection? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip textDetection? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute textDetection (TestVideo)\"}], \"Default\": \"textDetection Not Started (TestVideo)\"}, \"textDetection Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute textDetection (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-startTextDetection-1VKG25EE66L1I\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"textDetection Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"textDetection Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get textDetection Status (TestVideo)\"}, \"Get textDetection Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21Y5MQIU-checkTextDetection-1I7WEG7QGZLS0\", \"Next\": \"Did textDetection Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"textDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did textDetection Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"textDetection Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"textDetection Succeeded (TestVideo)\"}], \"Default\": \"textDetection Failed (TestVideo)\"}, \"textDetection Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"textDetection Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter Mediaconvert Media Type? (TestVideo)\", \"States\": {\"Filter Mediaconvert Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"Mediaconvert\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.Mediaconvert\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip Mediaconvert? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip Mediaconvert? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute Mediaconvert (TestVideo)\"}], \"Default\": \"Mediaconvert Not Started (TestVideo)\"}, \"Mediaconvert Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute Mediaconvert (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-StartMediaConvertFunctio-X0UUOJVL6AX2\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Mediaconvert Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Mediaconvert Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get Mediaconvert Status (TestVideo)\"}, \"Get Mediaconvert Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-CheckMediaConvertFunctio-1W0HFF4G4AYSD\", \"Next\": \"Did Mediaconvert Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"Mediaconvert Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did Mediaconvert Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"Mediaconvert Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"Mediaconvert Succeeded (TestVideo)\"}], \"Default\": \"Mediaconvert Failed (TestVideo)\"}, \"Mediaconvert Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"Mediaconvert Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}, {\"StartAt\": \"Filter technicalCueDetection Media Type? (TestVideo)\", \"States\": {\"Filter technicalCueDetection Media Type? (TestVideo)\": {\"Type\": \"Task\", \"Parameters\": {\"StageName.$\": \"$.Name\", \"Name\": \"technicalCueDetection\", \"Input.$\": \"$.Input\", \"Configuration.$\": \"$.Configuration.technicalCueDetection\", \"AssetId.$\": \"$.AssetId\", \"WorkflowExecutionId.$\": \"$.WorkflowExecutionId\", \"Type\": \"Video\", \"Status\": \"$.Status\"}, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-FilterOperationLambda-13QIESHVT8R0G\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"Skip technicalCueDetection? (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Skip technicalCueDetection? (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Started\", \"Next\": \"Execute technicalCueDetection (TestVideo)\"}], \"Default\": \"technicalCueDetection Not Started (TestVideo)\"}, \"technicalCueDetection Not Started (TestVideo)\": {\"Type\": \"Succeed\"}, \"Execute technicalCueDetection (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-startTechnicalCueDetecti-1NWCRDJLZP5LV\", \"ResultPath\": \"$.Outputs\", \"OutputPath\": \"$.Outputs\", \"Next\": \"technicalCueDetection Wait (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"technicalCueDetection Wait (TestVideo)\": {\"Type\": \"Wait\", \"Seconds\": 10, \"Next\": \"Get technicalCueDetection Status (TestVideo)\"}, \"Get technicalCueDetection Status (TestVideo)\": {\"Type\": \"Task\", \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorLibrary-JHH21-checkTechnicalCueDetecti-QY16N45OC9SS\", \"Next\": \"Did technicalCueDetection Complete (TestVideo)\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}], \"Catch\": [{\"ErrorEquals\": [\"States.ALL\"], \"Next\": \"technicalCueDetection Failed (TestVideo)\", \"ResultPath\": \"$.Outputs\"}]}, \"Did technicalCueDetection Complete (TestVideo)\": {\"Type\": \"Choice\", \"Choices\": [{\"Variable\": \"$.Status\", \"StringEquals\": \"Executing\", \"Next\": \"technicalCueDetection Wait (TestVideo)\"}, {\"Variable\": \"$.Status\", \"StringEquals\": \"Complete\", \"Next\": \"technicalCueDetection Succeeded (TestVideo)\"}], \"Default\": \"technicalCueDetection Failed (TestVideo)\"}, \"technicalCueDetection Failed (TestVideo)\": {\"Type\": \"Task\", \"End\": True, \"Resource\": \"arn:aws:lambda:us-west-2:123456789:function:mie-OperatorFailedLambda-16EEE1NGR8PH9\", \"ResultPath\": \"$\", \"Retry\": [{\"ErrorEquals\": [\"Lambda.ServiceException\", \"Lambda.AWSLambdaException\", \"Lambda.SdkClientException\", \"Lambda.Unknown\", \"MasExecutionError\"], \"IntervalSeconds\": 2, \"MaxAttempts\": 2, \"BackoffRate\": 2}]}, \"technicalCueDetection Succeeded (TestVideo)\": {\"Type\": \"Succeed\"}}}]}}}"
                            },
                            "ResourceType": {
                                "S": "STAGE"
                            },
                            "Name": {
                                "S": "TestVideo"
                            },
                            "Created": {
                                "S": "1605223690.391758"
                            },
                            "Metrics": {
                                "M": {

                                }
                            },
                            "Input": {
                                "M": {
                                    "Media": {
                                        "M": {
                                            "Thumbnail": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                    }
                                                }
                                            },
                                            "Audio": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                    }
                                                }
                                            },
                                            "Video": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            },
                                            "ProxyEncode": {
                                                "M": {
                                                    "S3Bucket": {
                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                    },
                                                    "S3Key": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "MetaData": {
                                        "M": {
                                            "MediaconvertJobId": {
                                                "S": "1605223698695-b3f1vm"
                                            },
                                            "Mediainfo_num_audio_tracks": {
                                                "S": "1"
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MediaconvertInputFile": {
                                                "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                            }
                                        }
                                    }
                                }
                            },
                            "Version": {
                                "S": "v0"
                            },
                            "MetaData": {
                                "M": {

                                }
                            },
                            "Next": {
                                "S": "TestAudio"
                            },
                            "Outputs": {
                                "L": [{
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "02d2238d01847fdc27cd62cf7b6852bf7e92e3006d0d31ac52c36c44e99a1ed2"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "celebrityRecognition"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "a82b144e3352648781ed444612f239626e8cf9b7dff80e3295688956dd6a845f"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "contentModeration"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "a312b02b9b02af24299b00d7f7155d75b432ba7097183b1f5b9ec727d9ddab78"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "faceDetection"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "e34c2c11579fb3e6bcbaf2ee720d8583cf6b03af0b0463d12d56349e8c062db8"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "labelDetection"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "a31cd826dfcf52cc577d7d4aa05eca8d2bea9a191986272230d0eb7cbce64629"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "personTracking"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "d13a20d30a77db60bcd2124c120a3677c288a5aa124e72304f20e87a82c89792"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "shotDetection"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "JobId": {
                                                        "S": "0f3b859196fb3c28f2374ffbe5bfe443fe08942d68afb4857ca3e7cfcad0d578"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "textDetection"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Input": {
                                                "M": {
                                                    "Media": {
                                                        "M": {
                                                            "Thumbnail": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                                                                    }
                                                                }
                                                            },
                                                            "Audio": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "Video": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                                    }
                                                                }
                                                            },
                                                            "ProxyEncode": {
                                                                "M": {
                                                                    "S3Bucket": {
                                                                        "S": "mie-dataplane-1s54zv3jhht0m"
                                                                    },
                                                                    "S3Key": {
                                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "MetaData": {
                                                        "M": {
                                                            "MediaconvertJobId": {
                                                                "S": "1605223698695-b3f1vm"
                                                            },
                                                            "Mediainfo_num_audio_tracks": {
                                                                "S": "1"
                                                            },
                                                            "AssetId": {
                                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                            },
                                                            "WorkflowExecutionId": {
                                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                            },
                                                            "MediaconvertInputFile": {
                                                                "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "Configuration": {
                                                "M": {
                                                    "MediaType": {
                                                        "S": "Video"
                                                    },
                                                    "Enabled": {
                                                        "BOOL": True
                                                    }
                                                }
                                            },
                                            "WorkflowExecutionId": {
                                                "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "MediaconvertJobId": {
                                                        "S": "1605223714672-o0nmx4"
                                                    },
                                                    "AssetId": {
                                                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                                    },
                                                    "WorkflowExecutionId": {
                                                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                                                    },
                                                    "MediaconvertInputFile": {
                                                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                                                    }
                                                }
                                            },
                                            "Media": {
                                                "M": {
                                                    "Audio": {
                                                        "M": {
                                                            "S3Bucket": {
                                                                "S": "mie-dataplane-1s54zv3jhht0m"
                                                            },
                                                            "S3Key": {
                                                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            "AssetId": {
                                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                                            },
                                            "Name": {
                                                "S": "Mediaconvert"
                                            }
                                        }
                                    },
                                    {
                                        "M": {
                                            "Status": {
                                                "S": "Complete"
                                            },
                                            "Media": {
                                                "M": {

                                                }
                                            },
                                            "MetaData": {
                                                "M": {
                                                    "JobId": {
                                                        "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                                                    }
                                                }
                                            },
                                            "Name": {
                                                "S": "technicalCueDetection"
                                            }
                                        }
                                    }
                                ]
                            },
                            "Id": {
                                "S": "83c40e0e-4996-4a73-ad5b-ff88569a6375"
                            },
                            "Operations": {
                                "L": [{
                                        "S": "celebrityRecognition"
                                    },
                                    {
                                        "S": "contentModeration"
                                    },
                                    {
                                        "S": "faceDetection"
                                    },
                                    {
                                        "S": "labelDetection"
                                    },
                                    {
                                        "S": "personTracking"
                                    },
                                    {
                                        "S": "shotDetection"
                                    },
                                    {
                                        "S": "textDetection"
                                    },
                                    {
                                        "S": "Mediaconvert"
                                    },
                                    {
                                        "S": "technicalCueDetection"
                                    }
                                ]
                            },
                            "AssetId": {
                                "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                            }
                        }
                    }
                }
            },
            "StaleOperations": {
                "L": [

                ]
            },
            "StaleStages": {
                "L": [

                ]
            },
            "StartAt": {
                "S": "TestPreprocess"
            },
            "StateMachineArn": {
                "S": "arn:aws:states:us-west-2:123456789:stateMachine:TestingWF-aqx5d8"
            },
            "Trigger": {
                "S": "api"
            },
            "Version": {
                "S": "v0"
            }
        }
    },
    "ApiVersion": {
        "S": "3.0.0"
    },
    "Id": {
        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
    },
    "AssetId": {
        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
    },
    "Globals": {
        "M": {
            "Media": {
                "M": {
                    "Text": {
                        "M": {
                            "S3Bucket": {
                                "S": "mie-dataplane-1s54zv3jhht0m"
                            },
                            "S3Key": {
                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/Translate.json"
                            }
                        }
                    },
                    "Thumbnail": {
                        "M": {
                            "S3Bucket": {
                                "S": "mie-dataplane-1s54zv3jhht0m"
                            },
                            "S3Key": {
                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_thumbnail.jpg"
                            }
                        }
                    },
                    "Audio": {
                        "M": {
                            "S3Bucket": {
                                "S": "mie-dataplane-1s54zv3jhht0m"
                            },
                            "S3Key": {
                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d/sample-video_audio.mp4"
                            }
                        }
                    },
                    "Video": {
                        "M": {
                            "S3Bucket": {
                                "S": "mie-dataplane-1s54zv3jhht0m"
                            },
                            "S3Key": {
                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                            }
                        }
                    },
                    "ProxyEncode": {
                        "M": {
                            "S3Bucket": {
                                "S": "mie-dataplane-1s54zv3jhht0m"
                            },
                            "S3Key": {
                                "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/sample-video_proxy.mp4"
                            }
                        }
                    }
                }
            },
            "MetaData": {
                "M": {
                    "comprehend_entity_job_id": {
                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                    },
                    "TranscribeJobId": {
                        "S": "transcribe-0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                    },
                    "Mediainfo_num_audio_tracks": {
                        "S": "1"
                    },
                    "WorkflowExecutionId": {
                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                    },
                    "output_uri": {
                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d//comprehend_entities/123456789-NER-6a65c759a9f2dcf6838ea782de3f95a7/output/output.tar.gz"
                    },
                    "MediaconvertJobId": {
                        "S": "1605223714672-o0nmx4"
                    },
                    "entity_output_uri": {
                        "S": "s3://mie-dataplane-1s54zv3jhht0m/private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/workflows/0c6c202a-dd21-4791-b7b1-28c0ab60575d//comprehend_entities"
                    },
                    "AssetId": {
                        "S": "c1752400-ba2f-4682-a8dd-6eba0932d148"
                    },
                    "JobId": {
                        "S": "80e47ace26091006ee243122cfe0d34ed2ac601d39c195570ceda621fc4ad828"
                    },
                    "comprehend_phrases_job_id": {
                        "S": "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
                    },
                    "MediaconvertInputFile": {
                        "S": "private/assets/c1752400-ba2f-4682-a8dd-6eba0932d148/input/upload/sample-video.mp4"
                    }
                }
            }
        }
    }
}

class awsmie:
    WORKFLOW_STATUS_QUEUED = "Queued"
    WORKFLOW_STATUS_STARTED = "Started"
    WORKFLOW_STATUS_WAITING = "Waiting"
    WORKFLOW_STATUS_RESUMED = "Resumed"
    WORKFLOW_STATUS_ERROR = "Error"
    WORKFLOW_STATUS_COMPLETE = "Complete"

    STAGE_STATUS_NOT_STARTED = "Not Started"
    STAGE_STATUS_STARTED = "Started"
    STAGE_STATUS_EXECUTING = "Executing"
    STAGE_STATUS_ERROR = "Error"
    STAGE_STATUS_COMPLETE = "Complete"

    OPERATION_STATUS_NOT_STARTED = "Not Started"
    OPERATION_STATUS_STARTED = "Started"
    OPERATION_STATUS_EXECUTING = "Executing"
    OPERATION_STATUS_ERROR = "Error"
    OPERATION_STATUS_COMPLETE = "Complete"
    OPERATION_STATUS_SKIPPED = "Skipped"

def get_sample_operation_input():
    return {
        "TableName": "testOperationTable",
        "Item": {
            "Name": test_operation_name,
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn",
            "StateMachineAsl": botocore.stub.ANY,
            "Version": "v0",
            "Id": botocore.stub.ANY,
            "Created": botocore.stub.ANY,
            "ResourceType": "OPERATION",
            "ApiVersion": "3.0.0"
        }
    }

def get_sample_operation_output():
    return {
        "Name": { "S": test_operation_name },
        "Type": { "S": "Async" },
        "Configuration": {
            "M": {
                "MediaType": { "S": "Video" },
                "Enabled": { "BOOL": True }
            }
        },
        "StartLambdaArn": { "S": "startArn" },
        "MonitorLambdaArn": { "S": "monitorArn" },
        "StateMachineAsl": { "S": '{"stateMachineAsl": "stateMachineAsl"}' },
        "Version": { "S": "v0" },
        "Id": { "S": "operation_id" },
        "Created": { "S": "created_date" },
        "ResourceType": { "S": "OPERATION" },
        "ApiVersion": { "S": "3.0.0" },
        "StageName": { "S": "_" + test_operation_name }
    }

def get_sample_stage_output():
    return {
        'Name': { 'S': '_testOperationName' },
        'Definition': { 'S': 'stageDefinition' }
    }

def get_sample_workflow():
    return {
        'Name': 'testWorkflowName',
        'StartAt': '_testOperationName',
        'Stages': {
            '_testOperationName': {
                'testOperationName-Asl'
            }
        },
        'Trigger': 'api',
        'Operations': [],
        'StaleStages': [],
        'Version': 'v0',
        'Id': 'id',
        'Created': 'created_timestamp',
        'Revisions': '1',
        'ResourceType': 'WORKFLOW',
        'ApiVersion': '3.0.0',

    }


# Stub Wrapper Functions
def stub_get_operation(stub, optional_input = None, optional_output = None):
    if optional_input == None:
        optional_input = {
            'TableName': 'testOperationTable',
            'Key': {
                'Name': test_operation_name
            },
            'ConsistentRead': botocore.stub.ANY
        }
    if optional_output == None:
        optional_output = { 'Item': get_sample_operation_output() }
    stub.add_response(
        'get_item',
        expected_params = optional_input,
        service_response = optional_output
    )

def stub_put_operation(stub, optional_input = None):
    if optional_input == None:
        optional_input = get_sample_operation_input()
    stub.add_response(
        'put_item',
        expected_params = optional_input,
        service_response = {}
    )

def stub_delete_operation(stub, optional_input = None):
    if optional_input == None:
        optional_input = {
            'TableName': 'testOperationTable',
            'Key': {
                'Name': test_operation_name
            }
        }
    stub.add_response(
        'delete_item',
        expected_params = optional_input,
        service_response = {}
    )

def stub_get_stage(stub, optional_input = None, optional_output = None):
    if optional_input == None:
        optional_input = {
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_testOperationName'
            },
            'ConsistentRead': botocore.stub.ANY
        }
    if optional_output == None:
        optional_output = { 'Item': get_sample_stage_output() }
    stub.add_response(
        'get_item',
        expected_params = optional_input,
        service_response = optional_output
    )

def stub_delete_stage(stub, optional_input = None):
    if optional_input == None:
        optional_input = {
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_' + test_operation_name
            }
        }
    stub.add_response(
        'delete_item',
        expected_params = optional_input,
        service_response = {}
    )

def stub_create_stage(stub):
    stub_get_stage(stub, optional_output={})
    stub_get_operation(
        stub,
        optional_input={
            'TableName': 'testOperationTable',
            'Key': {
                'Name': test_operation_name
            }
        }
    )

    stub.add_response(
        'put_item',
        expected_params = {
            'TableName': 'testStageTable',
            'Item': botocore.stub.ANY
        },
        service_response = {}
    )

def stub_put_role_policy(stub, optional_input = None):
    if optional_input == None:
        optional_input = {
            'RoleName': 'role',
            'PolicyName': test_operation_name,
            'PolicyDocument': json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "lambda:InvokeFunction",
                        "Resource": [
                            'startArn',
                            'monitorArn'
                        ]
                    }
                ]
            })
        }
    stub.add_response(
        'put_role_policy',
        expected_params = optional_input,
        service_response = {}
    )
