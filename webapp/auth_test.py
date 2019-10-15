import boto3

cognito = boto3.client('cognito-idp', region_name='us-east-1')

MIE_USERNAME = 'brandold@amazon.com'
MIE_PASSWORD = 'gB%6hqzS'
MIE_POOL_ID = 'us-east-1_Q5KU3dras'
MIE_CLIENT_ID = '4t2m07211eh1f36df0u9imscr4'


cognito_response = cognito.admin_initiate_auth(
    UserPoolId=MIE_POOL_ID,
    AuthFlow='ADMIN_NO_SRP_AUTH',
    AuthParameters={
        'USERNAME': MIE_USERNAME,
        'PASSWORD': MIE_PASSWORD
    },
    ClientId=MIE_CLIENT_ID
)


print(cognito_response)