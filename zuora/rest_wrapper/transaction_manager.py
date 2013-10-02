import json
import requests
from request_base import RequestBase


class TransactionManager(RequestBase):

    def get_invoices(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + \
                  'transactions/invoices/accounts/' + accountKey
        params = {
            'pageSize': pageSize
        }
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers)
        return self.get_json(response)
    
    def get_payments(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + \
                  'transactions/payments/accounts/' + accountKey
        params = {
            'pageSize': pageSize
        }
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers)
        return self.get_json(response)
    
    def invoice_and_collect(self, jsonParams):
        fullUrl = self.zuora_config.base_url + 'operations/invoice-collect'
        data = json.dumps(jsonParams)
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers)
        return self.get_json(response)
