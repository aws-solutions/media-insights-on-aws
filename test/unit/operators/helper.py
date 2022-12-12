def get_operator_parameter(metadata = {}, input = {}, media = {}):
    return {
        'Name': 'testName',
        'AssetId': 'testAssetId',
        'WorkflowExecutionId': 'testWorkflowId',
        'Configuration': {
            'Enabled': True,
            'MediaType': 'testMedia',
            'TargetLanguageCode': 'en',
            'TranscribeLanguage': 'en',
            'VocabularyName': 'testVocabularyName',
            'LanguageModelName': 'testLanguageModelName',
            'AllowDeferredExecution': False,
            'RedactionType': 'testRedactionType',
            'RedactionOutput': 'testRedactionOutput',
            'LanguageOptions': ['en'],
            'CollectionId': 'testCollectionId',
            'Bucket': 'testBucket',
            'Key': 'testKey'
        },
        'Status': 'testStatus',
        'MetaData': metadata,
        'Media': media,
        'Input': input
    }