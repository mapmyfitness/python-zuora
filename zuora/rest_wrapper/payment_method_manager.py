import config
import json
import requests


def createPaymentMethod(kwargs):
    fullUrl = config.baseUrl + 'payment-methods/credit-cards'

    if kwargs:
        data = json.dumps(kwargs)
    else:
        # No parameters were passed in
        print('No parameters were passed in')
        return None
    data = json.dumps(kwargs)

    response = requests.post(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def getPaymentMethods(accountKey, pageSize=10):
    fullUrl = config.baseUrl + 'payment-methods/credit-cards/accounts/' + \
              accountKey
    data = {'pageSize': pageSize}

    response = requests.get(fullUrl, params=data, headers=config.headers)
    return config.getJson(response)


def updatePaymentMethod(paymentMethodId, **kwargs):
    fullUrl = config.baseUrl + 'payment-methods/credit-cards/' + \
              paymentMethodId

    if kwargs:
        data = json.dumps(kwargs)
    else:
        # No parameters were passed in
        print('No parameters were passed in')
        return None

    response = requests.put(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def deletePaymentMethod(paymentMethodId):
    fullUrl = config.baseUrl + 'payment-methods/' + paymentMethodId

    response = requests.delete(fullUrl, headers=config.headers)
    return config.getJson(response)


### Test Methods ###
def testcreatePaymentMethod():
    print('Testing createPaymentMethod')
    params = {
        'accountKey': config.sampleAccountNumber,
        'creditCardType': 'Visa',
        'creditCardNumber': '4111111111111111',
        'expirationMonth': '10',
        'expirationYear': '2015',
        'securityCode': '123'
    }
    createResponse = createPaymentMethod(params)
    if createResponse:
        print('Success: ', createResponse['success'])
        if createResponse['success'] == True:
            print('Payment created successfully!')
            print('Payment Method Id: ', createResponse['paymentMethodId'])
        else:
            print('Payment was not created.')
            print('Reasons: ', createResponse['reasons'])
    else:
        print('Payment was not created (exceptions thrown).')


def testgetPaymentMethods():
    print('Testing getPaymentMethods')
    response = getPaymentMethods(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Payment Methods retrieved successfully')
            print('Credit Cards: ', response['creditCards'])
        else:
            print('Payment Methods were not retrieved successfully')


def testUpdatePaymentMethod():
    params = {
        'accountKey': config.sampleAccountNumber,
        'creditCardType': 'Visa',
        'creditCardNumber': '4111111111111111',
        'expirationMonth': '10',
        'expirationYear': '2015',
        'securityCode': '123'
    }
    createResponse = createPaymentMethod(params)
    paymentMethodId = createResponse['paymentMethodId']
    updateResponse = updatePaymentMethod(paymentMethodId,
                                         cardHolderName='NewCardholderName')
    if updateResponse:
        print('Success: ', updateResponse['success'])
        if updateResponse['success'] == True:
            print('Payment Method successfully updated')
            print('New Payment Method Id: ', updateResponse['paymentMethodId'])
        else:
            print('Payment Method was not updated')
    else:
        print('Payment method not updated. Errors thrown')


def testdeletePaymentMethod():
    params = {
        'accountKey': config.sampleAccountNumber,
        'creditCardType': 'Visa',
        'creditCardNumber': '4111111111111111',
        'expirationMonth': '10',
        'expirationYear': '2015',
        'securityCode': '123'
    }
    createResponse = createPaymentMethod(params)
    paymentMethodId = createResponse['paymentMethodId']
    deleteResponse = deletePaymentMethod(paymentMethodId)
    if deleteResponse:
        print('Success: ', deleteResponse['success'])
        if deleteResponse['success'] == True:
            print('Payment Method successfully deleted')
        else:
            print('Payment Method was not deleted')
    else:
        print('Errors were thrown')