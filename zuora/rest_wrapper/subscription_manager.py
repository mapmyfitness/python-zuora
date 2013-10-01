import config
import json
import requests

def getSubsByAcct(accountKey, pageSize = 10):
    fullUrl = config.baseUrl + 'subscriptions/accounts/' + accountKey
    data = { 'pageSize' : pageSize }

    response = requests.get(fullUrl, params=data, headers=config.headers)
    return config.getJson(response)


def getSubsByKey(subsKey):
    fullUrl = config.baseUrl + 'subscriptions/' + subsKey
    response = requests.get(fullUrl, headers=config.headers)
    return config.getJson(response)


def renewSub(subsKey, jsonParams={'invoiceCollect':False}):
    fullUrl = config.baseUrl + 'subscriptions/' + subsKey + '/renew'
    data = json.dumps(jsonParams)
    response = requests.put(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def cancelSub(subsKey,
              jsonParams={
                  'cancellationPolicy': config.defaultCancellationPolicy,
                  'invoiceCollect': False}):
    fullUrl = config.baseUrl + 'subscriptions/' + subsKey + '/cancel'
    data = json.dumps(jsonParams)
    response = requests.put(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def previewSubscription(jsonParams):
    fullUrl = config.baseUrl + 'subscriptions/preview'
    data = json.dumps(jsonParams)
    response = requests.post(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def createSubscription(jsonParams):
    fullUrl = config.baseUrl + 'subscriptions'
    data = json.dumps(jsonParams)
    response = requests.post(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


def updateSubscription(subsKey, jsonParams):
    fullUrl = config.baseUrl + 'subscriptions/' + subsKey
    data = json.dumps(jsonParams)
    response = requests.put(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


### Test Methods ###
def testgetSubsByAcct():
    print('Testing getSubsByAcct')
    response = getSubsByAcct(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Successfully retrieved Subscriptions')
            print('Subscriptions: ', response['subscriptions'])
        else:
            print('Subscriptions weren\'t retrieved')
            print('Reason: ', response['reasons'])
    else:
        print('Exceptions thrown. Test failed.')


def testgetSubsByKey():
    print('Testing getSubsByKey')
    response = getSubsByKey(config.sampleSubsNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Successfully retrieved Subscription')
            print('Subscription Id: ', response['id'])
        else:
            print('Subscriptions weren\'t retrieved')
            print('Reason: ', response['reasons'])
    else:
        print('Exceptions thrown. Test failed.')


def testrenewSub():
    print('Testing renewSub')
    response = renewSub(config.sampleSubsNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Successfully renewed subscription')
        else:
            print('Subscription was not renewed successfully')
            print('Reason: ', response['reasons'])
    else:
        print('Exceptions thrown. Test failed.')


def testcancelSub():
    print('Testing cancelSub')
    response = cancelSub('A-S00001734')
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Successfully canceled subscription')
        else:
            print('Subscription was not canceled successfully')
            print('Reason: ', response['reasons'])
    else:
        print('Exceptions thrown. Test failed.')
        