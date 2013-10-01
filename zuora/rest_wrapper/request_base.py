import requests


class RequestBase(object):
    def __init__(self, zuora_config):
        self.zuora_config = zuora_config

    def get_json(self, response):
        try:
            response.raise_for_status()
            print('Request Url: ', response.url)
            print('\nRequest headers: ', response.headers, '\n')
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return None
