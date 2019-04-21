from abc import ABCMeta, abstractmethod, abstractproperty
import hashlib
import logging
import time
import requests
import re
from typing import Union, Set

logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
API_TIMEOUT = 5

DEFAULT_TZ = 'America/New_York'

APP_VERSION = '2.5.1'
PHONE_BRAND = 'SM N9005'
PHONE_OS = 'Android'
MOBILE_ID = '1234567890123456'
USER_TYPE = '1'


def get_body(call: str):

    body_base = {}
    body_base['acceptLanguage'] = 'en'

    body_details = {}
    body_details['appVersion'] = APP_VERSION
    body_details['phoneBrand'] = PHONE_BRAND
    body_details['phoneOS'] = PHONE_OS
    body_details['traceId'] = str(int(time.time()))

    if call == 'login':
        body_base['devToken'] = ''
        body_base['userType'] = USER_TYPE
        body_base['method'] = 'login'
        return body_base
    elif call == 'devicelist':
        dev_list = dict(**body_base, **body_details)
        dev_list['method'] = 'devices'
        dev_list['pageNo'] = '1'
        dev_list['pageSize'] = '50'
        return dev_list


def get_head():
    header = {}
    header['accept-language'] = 'en'
    header['appVersion'] = APP_VERSION
    header['content-type'] = 'application/json'
    return header


def call_api(api: str, method: str, json: dict=None, headers: dict=None):
    response = None
    status_code = None
    try:
        logger.debug("[%s] calling '%s' api" % (method, api))
        if method == 'get':
            r = requests.get(API_BASE_URL + api, json=json,
                             headers=headers, timeout=API_TIMEOUT)
        elif method == 'post':
            r = requests.post(API_BASE_URL + api, json=json,
                              headers=headers, timeout=API_TIMEOUT)
        elif method == 'put':
            r = requests.post(API_BASE_URL + api, json=json,
                              headers=headers, timeout=API_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)
    else:
        if r.status_code == 200:
            status_code = 200
            response = r.json()
        else:
            logger.error("[%s] api call error with status code '%s' api"
                         % (api, status_code))
    finally:
        return (response, status_code)


def check_response(resp, call: str) -> bool:
    common_resp = ['get_devices', '15a_detail', '15a_toggle',
                   '15a_energy', 'walls_detail', 'walls_toggle',
                   '10a_detail', '10a_toggle', '10a_energy', '15a_ntlight'
                   ]
    if isinstance(resp, dict) and call in common_resp:
        if 'code' in resp and resp['code'] == 0:
            return True
    elif call == 'login' and 'code' in common_resp:
        if resp['code'] == 0 and 'result' in resp:
            return True
    elif call == '7a_detail' and 'deviceStatus' in resp:
        return True
    elif call == '7a_energy' and 'energyConsumptionOfToday' in resp:
        return True

    return False
