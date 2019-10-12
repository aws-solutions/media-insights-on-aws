import boto3
import os
import logging

cognito = boto3.client('cognito-idp')


if 'MIE_POOL_ID' in os.environ:
    MIE_POOL_ID = str(os.environ['MIE_POOL_ID'])
else:
    error = "ERROR: Cognito Pool Id must be in MIE_POOL_ID environment variable."
    print(error)
    logging.error("ERROR: Stack name must be in MIE_POOL_ID environment variable.")
    raise Exception(error)

if 'MIE_USERNAME' in os.environ:
    MIE_USERNAME = str(os.environ['MIE_USERNAME'])
else:
    error = "ERROR: Username must be in MIE_USERNAME environment variable."
    print(error)
    logging.error("ERROR: Stack name must be in MIE_USERNAME environment variable.")
    raise Exception(error)

if 'MIE_PASSWORD' in os.environ:
    MIE_PASSWORD = str(os.environ['MIE_PASSWORD'])
else:
    error = "ERROR: Password must be in MIE_PASSWORD environment variable."
    print(error)
    logging.error("ERROR: Stack name must be in MIE_PASSWORD environment variable.")
    raise Exception(error)

if 'MIE_CLIENT_ID' in os.environ:
    MIE_CLIENT_ID = str(os.environ['MIE_CLIENT_ID'])
else:
    error = "ERROR: Cognito Client Id must be in MIE_CLIENT_ID environment variable."
    print(error)
    logging.error("ERROR: Stack name must be in MIE_CLIENT_ID environment variable.")
    raise Exception(error)

try:
    cognito_response = cognito.admin_initiate_auth(
    AuthFlow='ADMIN_NO_SRP_AUTH',
    AuthParameters={
        'USERNAME': MIE_USERNAME,
        'PASSWORD': MIE_PASSWORD
    },
    ClientId=MIE_CLIENT_ID,
    UserPoolId=MIE_POOL_ID
    )
except Exception as e:
    print('received an error making the inital auth call: ', e)
else:
    try:
        token = cognito_response['AuthenticationResult']['IdToken']
    except KeyError as e:
        print('Missing token in auth response, trying to verify user')
        try:
            new_password = input('Enter a new password: ')
            new_password_response = cognito.admin_respond_to_auth_challenge(
                UserPoolId=MIE_POOL_ID,
                ClientId=MIE_CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    'NEW_PASSWORD': new_password,
                    'USER_ID_FOR_SRP': cognito_response['ChallengeParameters']['USER_ID_FOR_SRP'],
                    'USERNAME': MIE_USERNAME
                },
                Session=cognito_response['Session']
            )
        except Exception as e:
            raise Exception('Unable to set new password and verify user: ', e)
        else:
            final_cognito_response = cognito.admin_initiate_auth(
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': MIE_USERNAME,
                    'PASSWORD': new_password
                },
                ClientId=MIE_CLIENT_ID,
                UserPoolId=MIE_POOL_ID
            )
            try:
                token = final_cognito_response['AuthenticationResult']['IdToken']
            except KeyError as e:
                raise('Unable to complete authentication')
            else:
                print(token)
    else:
        print(token)
