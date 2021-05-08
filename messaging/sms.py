# https://www.raspberrypi-spy.co.uk/2012/08/sending-sms-text-messages-using-python/

import requests

from config import *


def send_sms(message):
    values = {'test': int(DEV_MODE),
              'username': TEXTLOCAL_USERNAME,
              'hash': TEXTLOCAL_API_HASH,
              'message': message,
              'sender': TEXTLOCAL_SENDER,
              'numbers': SMS_PHONE_NUMERS}

    url = 'https://api.txtlocal.com/send/'

    req = requests.get(url, params=values)
    if req.status_code != 200:
        raise Exception(f"Non-200 response {req.status_code}")
    print(req.text)
    print('Message sent')