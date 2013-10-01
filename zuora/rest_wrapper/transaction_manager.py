import config
import json
import requests


def getInvoices(accountKey, pageSize=10):
    fullUrl = config.baseUrl + 'transactions/invoices/accounts/' + accountKey
    params = {
        'pageSize': pageSize
    }
    response = requests.get(fullUrl, params=params, headers=config.headers)
    return config.getJson(response)


def getPayments(accountKey, pageSize=10):
    fullUrl = config.baseUrl + 'transactions/payments/accounts/' + accountKey
    params = {
        'pageSize': pageSize
    }
    response = requests.get(fullUrl, params=params, headers=config.headers)
    return config.getJson(response)


def invoiceAndCollect(jsonParams):
    fullUrl = config.baseUrl + 'operations/invoice-collect'
    data = json.dumps(jsonParams)
    response = requests.post(fullUrl, data=data, headers=config.headers)
    return config.getJson(response)


### Test Methods ###
def testgetInvoices():
    print('Testing getInvoices')
    response = getInvoices(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Invoices retrieved successfully.')


def testgetPayments():
    print('Testing getPayments')
    response = getPayments(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Payments retrieved successfully.')


def testinvoiceAndCollect():
    print('Testing invoiceAndCollect')
    params = {
        'accountKey': config.sampleAccountNumber,
    }
    response = invoiceAndCollect(params)
    if response:
        print('Success: ', response['success'])
        if response['success'] == True:
            print('Invoices and Payments generated successfully')
            print('Amount Collected: ', response['amountCollected']) 
        else:
            print('Invoices and Payments not generated.')
            print('Reasons: ', response['reasons'])
