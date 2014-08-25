import requests
from request_base import RequestBase, rest_client_reconnect


class UsageManager(RequestBase):

    @rest_client_reconnect
    def get_usage(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + 'usage/accounts/' + \
                  accountKey
        params = {'pageSize': pageSize}
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
