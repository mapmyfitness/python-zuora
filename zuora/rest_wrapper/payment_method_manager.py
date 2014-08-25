from request_base import RequestBase, rest_client_reconnect
import json
import requests


class PaymentMethodManager(RequestBase):

    @rest_client_reconnect
    def create_payment_method(self, **kwargs):
        fullUrl = self.zuora_config.base_url + 'payment-methods/credit-cards'
    
        if kwargs:
            data = json.dumps(kwargs)
        else:
            # No parameters were passed in
            print('No parameters were passed in')
            return None
        data = json.dumps(kwargs)
    
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def get_payment_methods(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + \
                  'payment-methods/credit-cards/accounts/' + accountKey
        data = {'pageSize': pageSize}
    
        response = requests.get(fullUrl, params=data,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def update_payment_method(self, paymentMethodId, **kwargs):
        fullUrl = self.zuora_config.base_url + \
                 'payment-methods/credit-cards/' + paymentMethodId
    
        if kwargs:
            data = json.dumps(kwargs)
        else:
            # No parameters were passed in
            print('No parameters were passed in')
            return None
    
        response = requests.put(fullUrl, data=data,
                                headers=self.zuora_config.headers,
                                verify=False
        )
        return self.get_json(response)
    
    @rest_client_reconnect
    def delete_payment_method(self, paymentMethodId):
        fullUrl = self.zuora_config.base_url + 'payment-methods/' + \
                  paymentMethodId
    
        response = requests.delete(fullUrl, headers=self.zuora_config.headers,
                                   verify=False)
        return self.get_json(response)
