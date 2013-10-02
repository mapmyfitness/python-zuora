import requests
from request_base import RequestBase


class UsageManager(RequestBase):

    def get_usage(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + 'usage/accounts/' + \
                  accountKey
        params = {'pageSize': pageSize}
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers)
        return self.get_json(response)
