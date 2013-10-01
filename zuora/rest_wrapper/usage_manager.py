import config
import requests


def getUsage(accountKey, pageSize=10):
    fullUrl = config.baseUrl + 'usage/accounts/' + accountKey
    params = {
        'pageSize': pageSize
    }
    response = requests.get(fullUrl, params=params, headers=config.headers)
    return config.getJson(response)


### Test Methods ###
def testgetUsage():
    print('Testing getUsage')
    response = getUsage(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
