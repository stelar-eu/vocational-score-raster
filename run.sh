#!/bin/bash

# Check if three arguments are provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <token> <endpoint_url> <id> <signature>"
    exit 2
fi

# Assign command-line arguments to variables
token="$1"
endpoint_url="$2"
id="$3"
signature="$4"

# Construct the first curl command with dynamic arguments and store the response in a variable
# Signature is used to gain access to any secret fields defined during the creation of the task.
# Secret fields are not accessible without a valid signature.
response=$(curl -s -L -X GET -H "Authorization: $token" "$endpoint_url/api/v2/tasks/$id/$signature/input")

echo "$response"

# Check if the curl request was successful
success=$(echo "$response" | jq -r '.success')
if [ "$success" != "true" ]; then
    echo "Curl request failed"
    exit 3
fi

# Extract the "result" part from the JSON response
result=$(echo "$response" | jq '.result')

# Store the "result" part into a file named "input.json"
echo "$result" > input.json

# Execute the tool
python main.py input.json output.json

# Perform the second curl request with replacements and store the response in a variable
output_json=$(<output.json)  # Read content of output.json file into a variable

echo "$output_json"

# Replace task_exec_id and output_json with variables. The signature is used to verify that the tool is authenticated.
# We will not be using token, as it may expire prior to tool completion.
response=$(curl -s -X POST -H "Content-Type: application/json" "$endpoint_url/api/v2/tasks/$id/output" -d "{\"signature\": \"$signature\" \"outputs\": $output_json}")

echo "$response"

# Check if the second curl request was successful
success=$(echo "$response" | jq -r '.success')
if [ "$success" != "true" ]; then
    echo "Second curl request failed"
    exit 4
fi

echo "Second curl request successful"
