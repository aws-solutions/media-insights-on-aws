# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MIE dataplane API
#
# PRECONDITIONS:
# MIE base stack must be deployed in your AWS account
#
# Boto3 will raise a deprecation warning (known issue). It's safe to ignore.
#
# USAGE:
#   ./run_tests.sh from the tests dir
#   
#
###############################################################################

import urllib3

# Testing data

session_nonpaginated_results = {
        "OperatorName": "samplenonpagresults",
        "WorkflowId": "test-123",
        "Results": {
            "Testing": "This is some test data"
        }
    }


session_paginated_results = {
        "OperatorName": "samplepagresults",
        "WorkflowId": "test-123",
        "Results": {
            "Labels": [{
                "Timestamp": 0,
                "Label": {
                    "Name": "Purple",
                    "Confidence": 54.41469192504883,
                    "Instances": [],
                    "Parents": []
                }
            }
            ]
        }
    }

# TODO: Add assert statements for status == success in api response json


def test_dataplane_api(dataplane_api):
    api = dataplane_api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create an asset

    print("Creating an asset in the dataplane")

    create_asset_response = api.create_asset()
    assert create_asset_response.status_code == 200
    asset = create_asset_response.json()
    asset_id = asset["AssetId"] 

    print("Successfully created asset in the dataplane: {asset}".format(asset=asset))

    # Add metadata to the asset

    print("Adding nonpaginated metadata to asset: {asset}".format(asset=asset_id))

    nonpaginated_post_response = api.post_metadata(asset_id, session_nonpaginated_results)
    assert nonpaginated_post_response.status_code == 200
    nonpaginated_post_results = nonpaginated_post_response.json()
    print("Successfully stored nonpaginated results for: {asset}".format(asset=asset_id))
    print(nonpaginated_post_results)

    print("Adding paginated metadata to asset: {asset}".format(asset=asset_id))

    pages_stored = 0
    while 2 > pages_stored:
        store_page_response = api.post_metadata(asset_id, session_paginated_results, paginate=True)
        assert store_page_response.status_code == 200
        print("Successfully stored a page of results")
        pages_stored += 1

    paginated_post_response = api.post_metadata(asset_id, session_paginated_results, paginate=True,
                                                end=True)
    assert paginated_post_response.status_code == 200
    paginated_post_results = paginated_post_response.json()
    print("Successfully stored paginated results for: {asset}".format(asset=asset_id))
    print(paginated_post_results)

    # TODO: This test is currently broken. Seems to be a real issue with the API that needs looked into.

    # Retrieve all metadata from the asset

    print("Retrieving all metadata for the asset: {asset}".format(asset=asset_id))
    
    cursor = None
    
    more_results = True
    while more_results:
        retrieve_metadata_response = api.get_all_metadata(asset_id, cursor)
        assert retrieve_metadata_response.status_code == 200
        retrieved_metadata = retrieve_metadata_response.json()
        print(retrieved_metadata)
        if "cursor" in retrieved_metadata:
            cursor = retrieved_metadata["cursor"]
        else:
            more_results = False
    print("Successfully retrieved all metadata for asset: {asset}".format(asset=asset_id))

    # Retrieve specific metadata from the asset

    print("Retrieving sample metadata for the asset: {asset}".format(asset=asset_id))

    retrieve_single_metadata_response = api.get_single_metadata_field(asset_id,
                                                                      session_nonpaginated_results)
    assert retrieve_single_metadata_response.status_code == 200

    retrieved_single_metadata = retrieve_single_metadata_response.json()
    print(
        "Retrieved {operator} results for asset: {asset}".format(operator=session_nonpaginated_results["OperatorName"],
                                                                 asset=asset_id))
    print(retrieved_single_metadata)

    # Validate asset checkout
    print("Checking out asset {asset}".format(asset=asset_id))
    checkout_response = api.checkout_asset(asset_id)
    assert checkout_response.status_code == 200
    
    print("Verifying that we cannot check out the same asset twice")
    checkout_response = api.checkout_asset(asset_id)
    assert checkout_response.status_code == 500
    
    # Validate checkout list
    print("Listing all checked out assets")
    list_checkouts_response = api.list_checkouts()
    assert list_checkouts_response.status_code == 200

    # Validate asset checkin
    print("Checking in asset {asset}".format(asset=asset_id))
    checkin_response = api.checkin_asset(asset_id)
    assert checkin_response.status_code == 200

    print("Verifying that we cannot check in an asset that is not checked out.")
    checkin_response = api.checkin_asset(asset_id)
    assert checkin_response.status_code == 500


    # Delete specific metadata

    print("Deleting specific metadata for the asset: {asset}".format(asset=asset_id))
    delete_metadata_response = api.delete_single_metadata_field(asset_id, session_nonpaginated_results)
    assert delete_metadata_response.status_code == 200
    deleted_metadata = delete_metadata_response.json()
    print("Successfully deleted metadata field: {operator} for asset: {asset}".format(
        operator=session_nonpaginated_results["OperatorName"], asset=asset_id))
    print(deleted_metadata)

    # Delete entire asset

    print("Deleting the asset from the dataplane")
    delete_asset_response = api.delete_asset(asset_id)
    assert delete_asset_response.status_code == 200
    deleted_asset = delete_asset_response.text
    print(deleted_asset)

    print("Dataplane API tests complete")

