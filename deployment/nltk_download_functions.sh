#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE: This script provides utility functions to download and verify the 
#           hash of NLTK pickles.
#
# PRELIMINARY:
#   Sourced from within another script.
#
# USAGE:
#   source "${path}/nltk_download_functions.sh"
#
#   Where ${path} is the directory containing this script. If the calling
#   script is in the same directory, use "$(dirname "${BASH_SOURCE[0]}")".
#   Example: source "$(dirname "${BASH_SOURCE[0]}")/nltk_download_functions.sh"
#
###############################################################################

verify_hash() {
    local file_path="$1"
    local expected_hash="$2"
    local actual_hash=$(sha256sum "$file_path" | awk '{print $1}')

    if [ "$actual_hash" != "$expected_hash" ]; then
        echo "Hash mismatch found for $file_path"
        echo "Expected: $expected_hash"
        echo "Found: $actual_hash"
        return 1
    else
        return 0
    fi
}

function download_punkt() {
    cleanup_punkt "${1}"
    echo "Starting download of punkt zip file..."

    local -r source_dir="${1}"
    local -r zip_url="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip"
    local -r zip_file="punkt.zip"
    # this hash was verified to be working, it may need to be updated if nltk ever updates punkt pickles
    local -r expected_hash="51c3078994aeaf650bfc8e028be4fb42b4a0d177d41c012b6a983979653660ec"
    local temp_dir

    # Download the punkt zip file
    if ! curl -sSL "$zip_url" -o "$zip_file"; then
        echo "Error: Failed to download the zip file."
        return 1
    fi

    echo "Verifying hash against the last known valid hash..."

    # Verify the hash
    if ! verify_hash "$zip_file" "$expected_hash"; then
        echo "Hash verification failed. Please check if the new punkt file is valid. Exiting."
        rm -f "$zip_file"
        return 1
    fi

    # Create a temporary directory for extraction
    temp_dir=$(mktemp -d)
    if [[ ! -d "$temp_dir" ]]; then
        echo "Error: Failed to create a temporary directory."
        rm -f "$zip_file"
        return 1
    fi

    # Extract the zip file into the temporary directory
    if ! unzip -q "$zip_file" -d "$temp_dir"; then
        echo "Error: Failed to unzip the file."
        rm -rf "$temp_dir"
        rm -f "$zip_file"
        return 1
    fi

    # Create the destination directory and copy files
    # interacting directly with the app under /operators/translate for now until more apps
    # within the solution need punkt pickles
    local -r dest_dir="$source_dir/operators/translate/nltk_data/tokenizers/punkt"
    mkdir -p "$dest_dir"
    cp -r "$temp_dir/punkt/PY3/"* "$dest_dir/"

    # Clean up temporary files
    rm -rf "$temp_dir"
    rm -f "$zip_file"

    echo "Punkt zip file downloaded and extracted successfully."
}

function cleanup_punkt() {
    local -r source_dir="${1}"
    local -r target_dir="$source_dir/operators/translate/nltk_data"

    echo "Starting cleanup process for punkt data..."

    # Check if the target directory exists
    if [[ -d "$target_dir" ]]; then
        # Attempt to remove the directory
        if rm -rf "$target_dir"; then
            echo "Successfully removed the nltk_data directory at $target_dir."
        else
            echo "Error: Failed to remove the nltk_data directory at $target_dir."
            return 1
        fi
    else
        echo "The directory $target_dir does not exist. No cleanup necessary."
    fi

    echo "Cleanup process completed."
    return 0
}
