################################################### Connecting to AWS
import os

import boto3

import json

################################################### Create random name for things

################################################### Parameters for Thing
defaultPolicyName = 'EmissionVehiclePolicy'


###################################################

def createThing(n):
    global thingClient
    device_name = "device_{}".format(n)
    thingResponse = thingClient.create_thing(
        thingName=device_name
    )

    thingArn = ''
    thingId = ''
    data = json.loads(json.dumps(thingResponse, sort_keys=False, indent=4))
    for element in data:
        if element == 'thingArn':
            thingArn = data['thingArn']
        elif element == 'thingId':
            thingId = data['thingId']

        createCertificate(n, device_name, thingArn)

def createCertificate(n, name, arn):
    global thingClient
    certResponse = thingClient.create_keys_and_certificate(
        setAsActive=True
    )
    data = json.loads(json.dumps(certResponse, sort_keys=False, indent=4))
    for element in data:
        if element == 'certificateArn':
            certificateArn = data['certificateArn']
        elif element == 'keyPair':
            PublicKey = data['keyPair']['PublicKey']
            PrivateKey = data['keyPair']['PrivateKey']
        elif element == 'certificatePem':
            certificatePem = data['certificatePem']
        elif element == 'certificateId':
            certificateId = data['certificateId']

    with open('device_{}.public.key'.format(n), 'w') as outfile:
        outfile.write(PublicKey)
    with open('device_{}.private.key'.format(n), 'w') as outfile:
        outfile.write(PrivateKey)
    with open('device_{}.cert.pem'.format(n), 'w') as outfile:
        outfile.write(certificatePem)

    response = thingClient.attach_policy(
        policyName=defaultPolicyName,
        target=certificateArn
    )
    response = thingClient.attach_thing_principal(
        thingName=name,
        principal=certificateArn
    )

    aws_account_id = os.getenv("aws_account_id")

    thingClient.add_thing_to_thing_group(
        thingGroupName='thing_group',
        thingGroupArn='arn:aws:iot:us-east-2:{}:thinggroup/thing_group'.format(aws_account_id),
        thingName=name,
        thingArn=arn,
        overrideDynamicGroups=True | False
    )


thingClient = boto3.client('iot')
for n in range(5):
    createThing(n)
