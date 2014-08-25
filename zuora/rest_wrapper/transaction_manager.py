import json
import requests
from request_base import RequestBase, rest_client_reconnect


class TransactionManager(RequestBase):

    @rest_client_reconnect
    def get_invoices(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + \
                  'transactions/invoices/accounts/' + accountKey
        params = {
            'pageSize': pageSize
        }
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def get_payments(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + \
                  'transactions/payments/accounts/' + accountKey
        params = {
            'pageSize': pageSize
        }
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def invoice_and_collect(self, jsonParams):
        fullUrl = self.zuora_config.base_url + 'operations/invoice-collect'
        data = json.dumps(jsonParams)
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)
