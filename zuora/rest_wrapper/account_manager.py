import json
import requests
from request_base import RequestBase, rest_client_reconnect

# For more information on parameters and responses, please see
# http://knowledgecenter.zuora.com/D_Zuora_APIs/REST_API/B_REST_API_reference/Accounts


class AccountManager(RequestBase):

    @rest_client_reconnect
    def create_account(self, **kwargs):
        fullUrl = self.zuora_config.base_url + 'accounts'
    
        if kwargs:
            data = json.dumps(kwargs)
        else:
            # No parameters were passed in
            return None
    
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def get_account_summary(self, accountKey):
        fullUrl = self.zuora_config.base_url + 'accounts/' + accountKey + \
                  '/summary'
    
        response = requests.get(fullUrl, headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def get_account(self, accountKey):
        fullUrl = self.zuora_config.baseUrl + 'accounts/' + accountKey
    
        response = requests.get(fullUrl, headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def update_account(self, accountKey, **kwargs):
        fullUrl = self.zuora_config.baseUrl + 'accounts/' + accountKey
    
        if kwargs:
            data = json.dumps(kwargs)
        else:
            data = None
    
        response = requests.put(fullUrl, data=data,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
