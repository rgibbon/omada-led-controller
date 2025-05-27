from datetime import datetime
from enum import Enum
from sys import exit
from os import path
import requests
import urllib3
import logging
import config
import json

logFile = path.join(path.dirname(path.realpath(__file__)), 'main.log')

logging.basicConfig(
    filename=logFile,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Disable SSL certificate warnings (for self-signed certs or dev environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def GetCredentials():
    url = f"{config.BASE_URL}/openapi/authorize/token"
    params = {"grant_type": "client_credentials"}
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "omadacId": config.OMADA_ID,
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET
    }

    response = requests.post(url, headers=headers, params=params, json=data, verify=False)
    response_dict = json.loads(response.text)

    statusCode = response.status_code
    errorCode = response_dict.get("errorCode")
    message = response_dict.get('msg')
    result = response_dict.get('result')

    if statusCode == 200 and errorCode == 0:
        logging.info(message)
        return result.get('accessToken')
    else:
        logging.info(f'Error: StatusCode: {statusCode} | Message: {message}')
        exit(1)


def is_LED_enabled(accessToken: str) -> bool:    
    url = f"{config.BASE_URL}/openapi/v1/{config.OMADA_ID}/sites/{config.SITE_ID}/led"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"AccessToken={accessToken}"
    }
    response = requests.get(url, headers=headers, verify=False)
    response_dict = json.loads(response.text)
    statusCode = response.status_code
    errorCode = response_dict.get("errorCode")
    message = response_dict.get('msg')
    result = response_dict.get('result')
    if statusCode == 200 and errorCode == 0:
        return result.get('enable')
    logging.error(message)
    exit(0)


def ToggleLEDs():
    accessToken = GetCredentials()
    enabled = is_LED_enabled(accessToken)

    hour = datetime.now().hour
    expected_enabled = True if hour >= config.ENABLE_TIME and hour < config.DISABLE_TIME else False

    # LEDs ON | HR >= ENABLE_TIME and < DISABLE_TIME
    if enabled and expected_enabled or not enabled and not expected_enabled:
        logging.info(f'No changes needed')
        exit(0)

    STATE = {
        True: "ON",
        False: "OFF"
    }

    logging.info(f'LEDs are {STATE[enabled]}. Should be {STATE[not enabled]}. Changing...')
    
    url = f"{config.BASE_URL}/openapi/v1/{config.OMADA_ID}/sites/{config.SITE_ID}/led"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"AccessToken={accessToken}"
    }
    data = {"enable": not enabled} 
    response = requests.put(url, headers=headers, json=data, verify=False)

    response_dict = json.loads(response.text)
    errorCode = response_dict.get("errorCode")
    message = response_dict.get('msg')
    
    logging.info(f'{message}')


ToggleLEDs()
