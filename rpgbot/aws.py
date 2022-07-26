from __future__ import annotations

import base64
import json
import logging
from time import sleep

import boto3
from botocore.exceptions import ClientError

from rpgbot.constants import instance_id

region_name = 'us-east-1'
logger = logging.getLogger(__name__)


def get_secret(region=region_name):
    secret_name = 'discord/token/rpgbot'

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name,
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side. Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret).get('token')
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'],
            )
            return json.loads(decoded_binary_secret).get('token')


def turn_on_foundry(region=region_name):
    session = boto3.session.Session()
    client = session.client(service_name='ec2', region_name=region)
    logger.info(f'Starting the Foundry Instance {instance_id}.')
    client.start_instances(InstanceIds=[instance_id])
    repetition = 0
    while repetition <= 12:
        sleep(10)
        status_response_dict = client.describe_instance_status(
            InstanceIds=[
                instance_id,
            ],
            IncludeAllInstances=True,
        )
        instance_response = status_response_dict.get('InstanceStatuses')[0]
        instance_status = instance_response.get('InstanceState').get('Code')
        if instance_status > 0:
            if instance_status > 16:
                return 'There was a problem starting the instance. Please inform @lowerlight'
            else:
                return 'Foundry has been started. Visit https://foundry.caprica.us/join'
        repetition += 1
    return "It's taking a while to start the instance. Please inform @lowerlight"


def turn_off_foundry(region=region_name):
    session = boto3.session.Session()
    client = session.client(service_name='ec2', region_name=region)
    logger.info(f'Stopping the Foundry instance {instance_id}.')
    client.stop_instances(InstanceIds=[instance_id])
    repetition = 0
    while repetition <= 12:
        sleep(10)
        status_response_dict = client.describe_instance_status(
            InstanceIds=[
                instance_id,
            ],
            IncludeAllInstances=True,
        )
        instance_response = status_response_dict.get('InstanceStatuses')[0]
        instance_status = instance_response.get('InstanceState').get('Code')
        if instance_status > 16:
            return 'Foundry has been stopped.'
        repetition += 1
    return "It's taking a while to stop the instance. Please inform @lowerlight"


def get_foundry_status(region=region_name):
    session = boto3.session.Session()
    client = session.client(service_name='ec2', region_name=region)

    status_response_dict = client.describe_instance_status(
        InstanceIds=[
            instance_id,
        ],
        IncludeAllInstances=True,
    )
    logger.debug(f'Foundry Status: {json.dumps(status_response_dict)}')
    instance_responses = status_response_dict.get('InstanceStatuses')
    if len(instance_responses) > 0:
        instance_status = instance_responses[0].get(
            'InstanceState',
        ).get('Name')
    else:
        instance_status = 'Instance does not exist - inform @lowerlight'
    return instance_status
