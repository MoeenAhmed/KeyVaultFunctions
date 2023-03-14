import logging
import azure.functions as func
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential
import datetime
import smtplib
import os
from email.message import EmailMessage
import http.client
import json
import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    logging.info('Python Timer Trigger function execution started.')
    
    # Key vault configuration
    tenantId = os.environ["tenantId"]
    clientId = os.environ["clientId"]
    clientSecret = os.environ["clientSecret"]
    KVUri = os.environ["KVUri"]

    # SMTP configuration
    subject = os.environ["Subject"]
    sentFrom = os.environ["sentFrom"]
    sentTo = os.environ["sentTo"]

    # Http function url
    httpFunctionUrl = os.environ["httpFunctionUrl"]

    credential = ClientSecretCredential(tenantId, clientId, clientSecret)
    client = SecretClient(vault_url=KVUri, credential=credential)
    secrets = client.list_properties_of_secrets()
    notificationMsg = ""

    for secret in  secrets:
        if secret.enabled == True:
            secretInfo = client.get_secret(secret.name)
            if secret.expires_on is not None:
                expiryDate = secretInfo.properties.expires_on
                expiryDate = secret.expires_on
                today = datetime.datetime.utcnow()
                diff = expiryDate.replace(tzinfo=None) - today.replace(tzinfo=None)
                if(diff.days  < 30):
                    msg = " Secret Name: "+secret.name+" Expire Date: "+secret.expires_on.strftime('%m/%d/%Y')
                    notificationMsg +=msg+"\r\r\n"

    if notificationMsg != "":
        print ("Secret that expired….", notificationMsg)
        connection = http.client.HTTPConnection(httpFunctionUrl, 80, timeout=10)
        print(connection)
        requestHeaders = {'Content-type': 'application/json'}
        requestBody = {
                "Subject": subject,
                "SentFrom":sentFrom,
                "SentTo":sentTo,
                "Body": notificationMsg
            }
        requestBodyJson = json.dumps(requestBody)
        connection.request('POST', httpFunctionUrl, requestBodyJson, requestHeaders)
        response = connection.getresponse()
        print(response.read().decode())
        connection.close()

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
