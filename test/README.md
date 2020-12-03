# Media Insights Engine Testing - How To

### Overview

MIE Framework has 3 types of tests:


*Unit:* Tests of each functional component of the framework at the code level, e.g. scope is the code itself, checks for introduction of bugs by syntax errors, whitespace issues, correct flow control and order of execution, etc

*These tests can be run locally without an MIE deployment. 

*Integration:* Tests of each functional component of the framework with the dependent cloud resources, e.g. scope is the ensure no bugs introduced by dependencies and that a change did not introduce a feature that is incompatible with dependencies

*These tests require MIE to be deployed.  

*End to End:* Tests of each functional component of the framework with each other and all dependencies, e.g. scope is the ensure all components work successfully to perform the expected function

*These tests require MIE to be deployed. 


You can find each of these within the `test` directory of the framework.


### Unit Tests

These tests are invoked by running the `run_unit.sh` script in the `test/unit` directory. The script takes a
positional argument for what component to run the tests on: 
* `./run_unit.sh workflowapi` 
* `./run_unit.sh dataplaneapi` 


### Integration tests

Before these tests are run, you must have a healthy MIE deployment in your
AWS account.

You also need to set the following environment variables:

* `MIE_REGION` - The AWS region your MIE deployment is in
* `MIE_STACK_NAME` - The name of your MIE Cloudformation stack
* `AWS_ACCESS_KEY_ID` - A valid AWS Access Key
* `AWS_SECRET_ACCESS_KEY` - A valid AWS Secret Access Key

*Note, the IAM credentials you specify must belong to an IAM principal that
has administrator permissions on the MIE API's.  

These tests are invoked by running the `run_integ.sh` script in the `test/integ` directory. The script takes a
positional argument for what component to run the tests on: 
* `./run_integ.sh workflowapi` 
* `./run_integ.sh dataplaneapi` 


### End to End tests

Before these tests are run, you must have a healthy MIE deployment in your
AWS account.

You also need to set the following environment variables:

* `MIE_REGION` - The AWS region your MIE deployment is in
* `MIE_STACK_NAME` - The name of your MIE Cloudformation stack
* `AWS_ACCESS_KEY_ID` - A valid AWS Access Key
* `AWS_SECRET_ACCESS_KEY` - A valid AWS Secret Access Key

*Note, the IAM credentials you specify must belong to an IAM principal that
has administrator permissions on the MIE API's.  

These tests are invoked by running the `run_e2e.sh` script in the `test/e2e` directory. The script takes a
positional argument for what component to run the tests on: 
* `./run_e2e.sh workflowapi` 
* `./run_e2e.sh dataplaneapi`


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




#### Dataplane API

| API Method | Unit | Integ | e2e |
| ------------- | ------------- | ---------- | -------- |
| `POST /create`  | ✅ | ✅ | ✅
| `POST /metadata/{asset_id}`  | ✅ | ✅ | ✅
| `GET /metadata/{asset}/{operator}`  | ❌ | ✅ | ✅
| `GET /metadata/{asset}`  | ❌ | ❌ | ❌
| `DELETE /metadata/{asset}/{operator}`  | ❌ | ✅ | ✅
| `DELETE /metadata/{asset}`  | ❌ | ✅ | ✅
