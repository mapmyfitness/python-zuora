import requests
from account_manager import AccountManager

## This file contains some parameters that will need to be changed to work in different tenants:
## REQUIRED PARAMS:
## username: change to an API user that has REST write capabilities
## password: change to the password of the API user
## defaultCancellationPolicy: choose between EndOfCurrentTerm, EndOfLastInvoicePeriod, SpecificDate. If using SpecificDate, the cancellationEffectiveDate field is required in the cancelSubscription call
##
## USED FOR TESTING PURPOSES (Not required)
## hpmCreditCardPaymentMethodId: change to the ID of the generic Credit Card in your Zuora tenant
## sampleAccountNumber: change to some Account Number in your Zuora tenant
## sampleSubsNumber: change to some Subscription Number in your Zuora tenant

#baseUrl = 'https://apisandbox-api.zuora.com/rest/v1/'
#username = 'rest.user@test.com'
#password = 'Zuora001!'

defaultCancellationPolicy = 'EndOfCurrentTerm'

#Payment Id of Default Credit Card (specific per tenant)
hpmCreditCardPaymentMethodId = '2c92c0f93cf64d94013cfe2d20db61a7'


class ZuoraConfig(object):
    def __init__(self, zuora_settings):
        for key, value in zuora_settings.items():
            setattr(self, key, value)
        self.default_cancellation_policy = 'EndOfCurrentTerm'
        self.headers = {'apiAccessKeyId': zuora_settings['username'],
                        'apiSecretAccessKey': zuora_settings['password'],
                        'Content-Type': 'application/json'}


class RestClient(object):
    def __init__(self, zuora_settings):
        self.zuora_config = ZuoraConfig(zuora_settings)
        self.login()
        self.account_manager = AccountManager(self.zuora_config)

    def login(self):
        fullUrl = self.zuora_config.base_url + 'connections'
    
        response = requests.post(fullUrl, headers=self.zuora_config.headers)
        return self.get_json(response)
