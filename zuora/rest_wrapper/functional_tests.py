from rest_client import RestClient

# Sample Account Number
# (specific per tenant, created to use for test functions)
sampleAccountNumber = 'A00000120'

# Sample Subscription Number
# (specific per tenant, created to use for test functions)
sampleSubsNumber = 'A-S00001735'


### Test Client Methods ###
def testlogin(zuora_settings):
    client = RestClient(zuora_settings)
    response = client.login()
    if response:
        print('No exceptions thrown')
        print('Success: ', response['success'])
    else:
        print('Exceptions thrown. Login failed.')


### Test Account Methods ###
def testcreateAccount():
    print('Testing createAccount')
    billToContact = {
        'address1': 'Test Addr 1',
        'address2': 'Test Addr 2',
        'firstName': 'NewFirst',
        'lastName': 'NewLast',
        'country': 'United States',
           'state': 'GA'
    }

    name = 'New Test Account'
    currency = 'USD'
    billCycleDay = 0
    autoPay = False

    createdResponse = createAccount(
            autoPay=autoPay, name=name,
            currency=currency,
            billCycleDay=billCycleDay,
            billToContact=billToContact,
            hpmCreditCardPaymentMethodId=config.hpmCreditCardPaymentMethodId)
    if createdResponse:
        print('Account created successfully')
        print('Success: ', createdResponse['success'])
        print('Account Id: ', createdResponse['accountId'])
    else:
        print('Account was not created')


def testgetAccount():
    print('Testing getAccount')
    response = getAccount(config.sampleAccountNumber)
    if response:
        print('Account retrieved successfully')
        print('Success: ', response['success'])
        print('Basic Info: ', response['basicInfo'])
    else:
        print('Account was not retrieved')


def testgetAccountSummary():
    print('Testing getAccountSummary')
    response = getAccountSummary(config.sampleAccountNumber)
    if response:
        print('Account retrieved successfully')
        print('Success: ', response['success'])
        print('Basic Info: ', response['basicInfo'])
    else:
        print('Account was not retrieved')


def testupdateAccount():
    print('Testing updateAccount')
    billToContact = {
        'address1': 'New Test Addr 1',
        'address2': 'New Test Addr 2',
        'firstName': 'NewFirstName',
        'lastName': 'NewLastName',
        'country': 'United States',
        'state': 'GA'
    }
    updateResponse = updateAccount(config.sampleAccountNumber,
                                   billToContact=billToContact)
    if updateResponse:
        print('Account updated successfully')
        print('Success: ', updateResponse['success'])
    else:
        print('Account was not updated')


### Test Catalog Methods ###
def testgetCatalog():
    pageSize = 5
    page1Catalog = getCatalog(pageSize=pageSize)
    if page1Catalog:
        print('\nProduct Catalog (page 1):')
        print(page1Catalog)

        if 'nextPage' in page1Catalog:
            print('\nnextPage value: ', page1Catalog['nextPage'])
            print('\nProduct Catalog (page 2):')
            page2Catalog = getCatalog(pageSize=pageSize, page=2)
            print (page2Catalog)
    else:
        print('No Product Catalog was returned')


### Test Payment Method Methods ###
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


### Test Subscription Methods ###
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


### Test Transaction Methods ###
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


### Test Usage Methods ###
def testgetUsage():
    print('Testing getUsage')
    response = getUsage(config.sampleAccountNumber)
    if response:
        print('Success: ', response['success'])
