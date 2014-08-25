import json
import requests

import logging
log = logging.getLogger(__name__)

from request_base import RequestBase, rest_client_reconnect


class SubscriptionManager(RequestBase):

    @rest_client_reconnect
    def get_subscriptions_by_account(self, accountKey, pageSize=10):
        fullUrl = self.zuora_config.base_url + 'subscriptions/accounts/' + \
                  accountKey
        data = {'pageSize': pageSize}
    
        response = requests.get(fullUrl, params=data,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)

    @rest_client_reconnect
    def get_subscriptions_by_key(self, subsKey):
        fullUrl = self.zuora_config.base_url + 'subscriptions/' + subsKey
        response = requests.get(fullUrl, headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def renew_subscription(self, subsKey,
                           jsonParams={'invoiceCollect': False}):
        fullUrl = self.zuora_config.base_url + 'subscriptions/' + subsKey + \
                  '/renew'
        data = json.dumps(jsonParams)
        response = requests.put(fullUrl, data=data,
                                headers=self.zuora_config.headers,
                                verify=False
        )
        return self.get_json(response)
    
    @rest_client_reconnect
    def cancel_subscription(self, subsKey, jsonParams={}):
        jsonParams.setdefault('cancellationPolicy',
                              self.zuora_config.default_cancellation_policy)
        fullUrl = self.zuora_config.base_url + 'subscriptions/' + subsKey + \
                  '/cancel'
        data = json.dumps(jsonParams)
        log.info("Zuora REST: Canceling subscription: %s" % subsKey)
        response = requests.put(fullUrl, data=data,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def preview_subscription(self, jsonParams):
        fullUrl = self.zuora_config.base_url + 'subscriptions/preview'
        data = json.dumps(jsonParams)
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def create_subscription(self, jsonParams):
        fullUrl = self.zuora_config.base_url + 'subscriptions'
        data = json.dumps(jsonParams)
        response = requests.post(fullUrl, data=data,
                                 headers=self.zuora_config.headers,
                                 verify=False)
        return self.get_json(response)
    
    @rest_client_reconnect
    def update_subscription(self, subsKey, jsonParams):
        fullUrl = self.zuora_config.base_url + 'subscriptions/' + subsKey
        data = json.dumps(jsonParams)
        response = requests.put(fullUrl, data=data,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
        