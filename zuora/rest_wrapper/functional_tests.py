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