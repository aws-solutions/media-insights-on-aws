import boto3
import os
import logging
import sys


def return_token(token):
    print(token)
    sys.exit(0)

if 'MIE_POOL_ID' in os.environ:
    MIE_POOL_ID = str(os.environ['MIE_POOL_ID'])
else:
    error = "ERROR: Cognito Pool Id must be in MIE_POOL_ID environment variable."
    logging.error(error)
    sys.exit(1)

if 'MIE_USERNAME' in os.environ:
    MIE_USERNAME = str(os.environ['MIE_USERNAME'])
else:
    error = "ERROR: Username must be in MIE_USERNAME environment variable."
    logging.error(error)
    sys.exit(1)

if 'MIE_PASSWORD' in os.environ:
    MIE_PASSWORD = str(os.environ['MIE_PASSWORD'])
else:
    error = "ERROR: Password must be in MIE_PASSWORD environment variable."
    logging.error(error)
    sys.exit(1)

if 'MIE_CLIENT_ID' in os.environ:
    MIE_CLIENT_ID = str(os.environ['MIE_CLIENT_ID'])
else:
    error = "ERROR: Cognito Client Id must be in MIE_CLIENT_ID environment variable."
    logging.error("ERROR: Stack name must be in MIE_CLIENT_ID environment variable.")
    sys.exit(1)


if 'REGION' in os.environ:
    region = str(os.environ['REGION'])
else:
    error = "ERROR: REGION must be in REGION environment variable."
    logging.error(error)
    sys.exit(1)

if 'AWS_PROFILE' in os.environ:
    profile = str(os.environ['AWS_PROFILE'])
else:
    profile = 'default'

session = boto3.session.Session(profile_name=profile)
cognito = session.client('cognito-idp', region_name=region)


def main():
    tty = os.open("/dev/tty", os.O_RDWR)
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
        logging.error('Unable to initiate auth call: ', e, MIE_POOL_ID, MIE_CLIENT_ID)
        sys.exit(1)
    else:
        try:
            token = cognito_response['AuthenticationResult']['IdToken']
        except KeyError:
            try:
                os.write(tty, "\nEnter a new password: ".encode('utf-8'))
                new_password = input("")
                cognito.admin_respond_to_auth_challenge(
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
                logging.error('Unable to set new password and verify user: ', e)
                sys.exit(1)
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
                    logging.error('Unable to complete authentication workflow: ', e)
                    sys.exit(1)
                else:
                    return_token(token)
        else:
            return_token(token)


if __name__ == "__main__":
    main()

