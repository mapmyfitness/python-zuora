import requests
from functools import wraps

import logging
log = logging.getLogger(__name__)


def rest_client_reconnect(fn):
    """Tries to re-login if the REST request fails.
       Only works with RequestBase methods
    """
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        response = fn(self, *args, **kwargs)
        # If it worked just fine, return the response
        if response.get('success'):
            return response
        # Otherwise, try to login, and then retry the call
        else:
            self.login()
            log.info("Zuora: Re-logged in through REST client.")
            return fn(self, *args, **kwargs)
    return wrapped


class RequestBase(object):
    def __init__(self, zuora_config):
        self.zuora_config = zuora_config

    def login(self):
        fullUrl = self.zuora_config.base_url + 'connections'
        response = requests.post(fullUrl, headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)

    def get_json(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return None
