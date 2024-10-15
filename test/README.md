# Media Insights on AWS Testing - How To

### Overview

MI Framework has 3 types of tests:


*Unit:* Tests of each functional component of the framework at the code level. Scope is the code itself, checks for introduction of bugs by syntax errors, whitespace issues, correct flow control and order of execution, etc

Unit tests can be run locally without an MI deployment. 

*Integration:* Tests of each functional component of the framework with the dependent cloud resources in order to ensure no bugs have been introduced by dependencies and to ensure that a change did not introduce a feature that is incompatible with dependencies.

* Ensures the workflowapi is able to create state machines and perform CRUD operations on dynamodb
* ensures boto3 proxy functions run successfully

Integration tests require MI to be deployed.  

*End to End:* Tests of each functional component of the framework with each other and all dependencies. Scope is the ensure all components work successfully to perform the expected function, e.g. ensure the workflowapi can successfully communicate with the dataplaneapi and successfully complete a workflow

End to end tests require MI to be deployed. 


You can find each of these within the `test` directory of the framework.


### Unit Tests

These tests are invoked by running the `run_unit.sh` script in the `test/unit` directory. The script optionally takes a
positional argument for what component to run the tests on: 
* `./run_unit.sh workflowapi` 
* `./run_unit.sh dataplaneapi`

Otherwise it runs all available unit tests when no arguments are passed


### Integration tests

Before these tests are run, you must have a healthy MI deployment in your
AWS account.

You also need to set the following environment variables:

* `REGION` - The AWS region your MI deployment is in
* `MI_STACK_NAME` - The name of your MI Cloudformation stack
* `AWS_ACCESS_KEY_ID` - A valid AWS Access Key
* `AWS_SECRET_ACCESS_KEY` - A valid AWS Secret Access Key

If you are using temporary STS credentials, you also need to set the session token:

* `AWS_SESSION_TOKEN` - For use with STS temporary credentials

*Note, the IAM credentials you specify must belong to an IAM principal that
has administrator permissions on the MI API's.  

These tests are invoked by running the `run_integ.sh` script in the `test/integ` directory. The script takes a
positional argument for what component to run the tests on: 
* `./run_integ.sh workflowapi` 
* `./run_integ.sh dataplaneapi` 


### End to End tests

Before these tests are run, you must have a healthy MI deployment in your
AWS account.

You also need to set the following environment variables:

* `REGION` - The AWS region your MI deployment is in
* `MI_STACK_NAME` - The name of your MI Cloudformation stack
* `AWS_ACCESS_KEY_ID` - A valid AWS Access Key
* `AWS_SECRET_ACCESS_KEY` - A valid AWS Secret Access Key

If you are using temporary STS credentials, you also need to set the session token:

* `AWS_SESSION_TOKEN` - For use with STS temporary credentials

*Note, the IAM credentials you specify must belong to an IAM principal that
has administrator permissions on the MI API's.  

These tests are invoked by running the `run_e2e.sh` script in the `test/e2e` directory.  
* `./run_e2e.sh`

The pytest command in that script will run all files of the form test_*.py or *_test.py in the current directory and its subdirectories.

### Coverage

#### Workflow API

| API Method | Unit | Integ | e2e |
| ------------- | ------------- | ---------- | -------- |
| `POST /workflow/execution`  | ✅ | ❌ | ✅
| `GET /workflow/execution/{AssetId}`  | ✅ | ❌ | ❌
| `GET /workflow/execution/{Id}`  | ✅ | ❌ | ✅
| `POST /system/configuration`  | ❌ | ❌ | ❌
| `GET /system/configuration`  | ❌ | ❌ | ❌
| `GET /workflow/operation/`  | ❌ | ✅ | ✅
| `POST /workflow/operation/`  | ❌ | ✅ | ❌
| `DELETE /workflow/operation/`  | ❌ | ✅ | ❌
| `GET /workflow/`  | ❌ | ❌ | ✅
| `POST /workflow/`  | ❌ | ✅ | ✅
| `DELETE /workflow/`  | ❌ | ✅ | ✅
| `GET /workflow/stage`  | ❌ | ✅ | ✅
| `POST /workflow/stage`  | ❌ | ✅ | ✅
| `DELETE /workflow/stage`  | ❌ | ✅ | ✅
| `GET /workflow/configuruation`  | ❌ | ❌ | ✅
| `POST /service/translate/get_terminology`  | ❌ | ✅ | ❌
| `POST /service/translate/download_terminology`  | ❌ | ✅ | ❌
| `GET /service/translate/list_terminologies`  | ❌ | ✅ | ❌
| `POST /service/translate/delete_terminology`  | ❌ | ✅ | ❌
| `POST /service/translate/create_terminology`  | ❌ | ✅ | ❌
| `POST /service/translate/get_parallel_data`  | ❌ | ✅ | ❌
| `GET /service/translate/list_parallel_data`  | ❌ | ✅ | ❌
| `POST /service/translate/download_parallel_data`  | ❌ | ✅ | ❌
| `POST /service/translate/delete_parallel_data`  | ❌ | ✅ | ❌
| `POST /service/translate/create_parallel_data`  | ❌ | ✅ | ❌
| `GET /service/transcribe/list_language_models`  | ❌ | ✅ | ❌
| `POST /service/transcribe/describe_language_model`  | ❌ | ✅ | ❌


#### Dataplane API

| API Method | Unit | Integ | e2e |
| ------------- | ------------- | ---------- | -------- |
| `POST /create`  | ✅ | ✅ | ✅
| `POST /metadata/{asset_id}`  | ✅ | ✅ | ✅
| `GET /metadata/{asset}/{operator}`  | ❌ | ✅ | ✅
| `GET /metadata/{asset}`  | ❌ | ❌ | ❌
| `DELETE /metadata/{asset}/{operator}`  | ❌ | ✅ | ✅
| `DELETE /metadata/{asset}`  | ❌ | ✅ | ✅
