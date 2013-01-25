"""
    Zuora Interface Module
    ~~~~~~~~~~~~~~~~~~~~~~

    Current WSDL files are based on Zuora WSDL 39.

    Accounts for our Zuora setup are fetch by either A-user_id (i.e. A-32432)
    or just by the user id (look at the get_account WHERE clause).

    We also use custom fields in some of our queries: CustomField__c that
    could break for people who don't use our custom fields (i.e. ShortCode__c)

    Usage example:
    import zuora

    z = zuora.Zuora(SETTINGS)
    account = z.get_account(23432)
"""
from datetime import datetime, date
from os import path
import re
import errno
import socket

from suds import WebFault
from suds.client import Client
from suds.sax.element import Element
from suds.xsd.doctor import Import, ImportDoctor

import logging
log = logging.getLogger(__name__)

# Tell suds to stop logging and stfu (it logs noise as errors)
log_suds = logging.getLogger('suds')
log_suds.propagate = False


class ZuoraException(Exception):
    """This is our base exception for the Zuora lib"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)

class DoesNotExist(ZuoraException):
    """
    Exception for when objects don't exist in Zuora
    """
    pass

class MissingRequired(ZuoraException):
    """
    Exception for when a required parameter is missing
    """
    pass


# main class
class Zuora:

    #: Soap Service Client
    client = None

    #: Currency
    currency = 'USD'

    #: SessionID (TODO: put this into memcache)
    session_id = None

    def __init__(self, zuora_settings):
        """
        Usage example:

        Required dictionary settings for zuora client:

        username : str : username for logging into Zuora
        password : str : password for logging into Zuora
        wsdl_file : str : path to local wsdl file used for suds library

        Optional dictionary settings:

        gateway_name : str : The name of the gateway used for payment
                             authorization
        test_users : str : Used if you only desire to create test user
                           accounts. Adds the custom field Test_Account__c
                           to all created users.
        """
        # Assign settings
        self.username = zuora_settings["username"]
        self.password = zuora_settings["password"]
        self.wsdl_file = zuora_settings["wsdl_file"]
        self.base_dir = path.dirname(__file__)
        self.authorize_gateway = zuora_settings.get("gateway_name", None)
        self.create_test_users = zuora_settings.get("test_users", None)

        # Build Client
        imp = Import('http://object.api.zuora.com/')
        imp.filter.add('http://api.zuora.com/')
        imp.filter.add('http://fault.api.zuora.com/')
        schema_doctor = ImportDoctor(imp)

        wsdl_file = 'file://%s' % path.abspath(
                                    self.base_dir + "/" + self.wsdl_file)

        self.client = Client(url=wsdl_file, doctor=schema_doctor,
                             cache=None)

        # Force No Cache
        self.client.set_options(cache=None)

    # Client Create
    def call(self, fn, *args, **kwargs):
        """
        Wraps the Error handling for the client call.
        :param function fn: function to call (ie., self.client.service.delete)

        :returns: the client response
        """
        retry = False
        kwargs['initial_retry'] = kwargs.get('initial_retry', datetime.now())
        last_restry = kwargs.get('last_retry', datetime.now())
        try:
            response = fn(*args, **kwargs)
        except WebFault as err:
            if err.fault.faultcode == "fns:INVALID_SESSION":
                self.login()
                try:
                    response = fn(*args, **kwargs)
                except Exception as error:
                    log.error("Zuora: Unexpected Error. %s" % error)
                    raise ZuoraException("Zuora: Unexpected Error. %s"\
                                         % error)
            else:
                log.error("WebFault. Invalid Session. %s" % err.__dict__)
                raise ZuoraException("WebFault. Invalid Session. %s"\
                                    % err.__dict__)
        # If the connection to Zuora drops out, retry
        except socket.error, e:
            # A socket error
            retry = True
            log.error("Zuora Socket error. Retry attempt: %s" % retry_attempt)
        except IOError, e:
            if e.errno == errno.EPIPE:
                # EPIPE error
                log.error("Zuora Broken pipe. Retry attempt: %s" \
                          % retry_attempt)
            else:
                # Other error
                log.error("IOError %s. Retry attempt: %s" \
                          % (e.errno, retry_attempt))
            retry = True
        except Exception as error:
            log.error("Zuora: Unexpected Error. %s" % error)
            raise ZuoraException("Zuora: Unexpected Error. %s" % error)

        # Retry the same call up to three times
        if retry:
            initial_delta = datetime.now() - kwargs['initial_retry']
            last_delta = datetime.now() - last_restry
            # If we haven't surpassed a maximum retry limit of 10 seconds
            # And the last retry was more than two seconds ago
            if initial_delta.seconds < 10 and last_delta.seconds > 2:
                # Set the last retry to now and retry again
                kwargs['last_retry'] = datetime.now()
                return self.call(fn, *args, **kwargs)
            else:
                raise ZuoraException("Zuora request reached max retry time.")
            
        return response

    # Client Create
    def create(self, z_object):
        """
        Use create() to create one or more objects of a specific type.
        You can specify different types in different create() calls, but
        each create() call must apply to only one type of object.

        :param z_object z_object: object to create

        :returns: the API response
        """

        # Call Create
        fn = self.client.service.create
        response = self.call(fn, z_object)

        # return the response
        return response

    def delete(self, obj_type, id_list=[]):
        """
        Deletes one or more objects of the same type. You can specify different
        types in different deletecalls, but each delete call must only apply to
        one type of object.

        :param str type: The type of object that you are deleting.
        :param list id_list: A list of ids for the objects you want to delete.

        :returns: the API response
        """

        # Call Update
        fn = self.client.service.delete
        response = self.call(fn, obj_type, id_list)

        # return the response
        return response

    # Client Login
    def login(self):
        """
        Creates the SOAP SessionHeader with the correct session_id from Zuora

        TODO: investigate methodology to persist session_id across sessions
        - look at custom capabilities -- sqlalchemy caching - WEB-935 perhaps
        """
        login_response = self.client.service.login(username=self.username,
                                                   password=self.password)
        self.session_id = login_response.Session

        # Define Session Namespace
        session_namespace = ('ns1', 'http://api.zuora.com/')

        # Create a session element to hold the value of result.Session
        # from our login call
        session = Element('session', ns=session_namespace)\
                    .setText(self.session_id)

        # Create a session_header element to enclose the session element
        SessionHeader = Element('SessionHeader', ns=session_namespace)

        # Append the session element inside the session_header element
        SessionHeader.append(session)
        self.client.set_options(soapheaders=[SessionHeader])

    def query(self, query_string):
        """
        Pass the zosql querystring into the query() SOAP method
        TODO: add retry_count to keep loop of doom out of picture
        TODO: investigate faultcodes for different error handling
        TODO: option: everytime you capability.create you check if alive

        :param string query_string: ZQL query string

        :returns: the API response
        """

        # format query string (remove linebreaks, tabs, etc.)
        query_string = ' '.join(query_string.split())

        # Call Query
        fn = self.client.service.query
        response = self.call(fn, queryString=query_string)

        # return the response
        return response

    def query_more(self, query_locator):
        """
        Use queryMore() to request additional results from a previous
        query() call. If your initial query() call returns more
        than 2000 results, you can use queryMore() to query for more
        the additional results

        :param string query_string: ZQL query string

        :returns: the API response
        """

        # Call Query
        fn = self.client.service.queryMore
        response = self.call(fn, queryLocator=query_locator)

        # return the response
        return response

    def update(self, z_object):
        """
        Updates the information in one or more objects of the same type. You
        can specify different types of objects in different update() calls,
        but each specific update() call must apply to one type of object.

        :param z_object z_object: object to create

        :returns: the API response
        """

        # Call Update
        fn = self.client.service.update
        response = self.call(fn, z_object)

        # return the response
        return response

    def create_product_amendment(self, effective_date, subscription_id,
                                  name_prepend, amendment_type,
                                  status="Draft"):
        """
        Creates a new product amendment and adds an id for the new
        amendment
        """
        # Make Amendment
        zAmendment = self.client.factory.create('ns2:Amendment')
        zAmendment.EffectiveDate = effective_date
        zAmendment.Name = "%s %s" % (name_prepend, effective_date)
        zAmendment.Status = status
        zAmendment.SubscriptionId = subscription_id
        zAmendment.Type = amendment_type

        # Create Amendment
        response = self.create(zAmendment)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error creating Amendment. %s" % response)
        zAmendment.Id = response[0].Id

        return zAmendment

    def update_product_amendment(self, effective_date, zAmendment,
                                 status='Completed'):
        """
        Updates a product amendment and returns the update response
        """
        zAmendmentUpdate = self.client.factory.create('ns2:Amendment')
        zAmendmentUpdate.Id = zAmendment.Id
        zAmendmentUpdate.ContractEffectiveDate = effective_date
        zAmendmentUpdate.Status = status
        response = self.update(zAmendmentUpdate)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error update Amendment. %s" % response)

        # return
        return response

    def add_product_amendment(self, name, subscription_id,
                              product_rate_plan_id):
        """
        Use Amendment to make changes to a subscription. For example, if you
        wish to change the terms and conditions of a subscription, you would
        use an Amendment.

        :param str name: A name for the amendment. (100 chars)
        :param str subscription_id: The identification number for the\
            subscription that is being amended.
        :param str product_rate_plan_id: ProductRatePlanID

        :returns: response
        """
        effective_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        # Create the new product amendment
        zAmendment = self.create_product_amendment(
                                        effective_date,
                                        subscription_id,
                                        name_prepend="New Product Amendment",
                                        amendment_type='NewProduct')

        # Make Rate Plan
        zRatePlan = self.client.factory.create('ns0:RatePlan')
        zRatePlan.AmendmentType = "NewProduct"
        zRatePlan.AmendmentId = zAmendment.Id
        zRatePlan.ProductRatePlanId = product_rate_plan_id
        response = self.create(zRatePlan)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error creating RatePlan. %s" % response)

        # Update the product amendment
        response = self.update_product_amendment(effective_date, zAmendment)

        # return
        return response

    def cancel_subscription(self, subscription_id):
        """
        Canceling a Subscription (using Amendment)

        :param str subscription_id: The identification number for the\
            subscription that is being amended.

        :returns: response
        """
        subscriptions = self.get_subscriptions(subscription_id=subscription_id)
        if subscriptions:
            effective_date_str = subscriptions[0]['SubscriptionEndDate']
            effective_date = effective_date_str
        else:
            effective_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        # Create the product cancellation amendment
        zAmendment = self.create_product_amendment(
                                        effective_date,
                                        subscription_id,
                                        name_prepend="Subscription Cancel",
                                        amendment_type='Cancellation')

        # Update the product amendment
        response = self.update_product_amendment(effective_date, zAmendment)
        return response

    def create_active_account(self, zAccount=None, zContact=None,
                              payment_method_id=None, user=None,
                              billing_address=None, shipping_address=None,
                              site_name=None):
        """
        Create an Active Account for use in Subscribe()
        """
        # Create Account if it doesn't exist
        if not zAccount:
            zAccount = self.make_account(user=user, site_name=site_name)

        # Create Bill-To Contact on Account
        if not zContact:
            zContact = self.make_contact(user=user,
                                         billing_address=billing_address,
                                         zAccount=zAccount)
        
        # Add the shipping contact if it exists
        if shipping_address:
            zShippingContact = self.make_contact(user=user,
                                         billing_address=shipping_address,
                                         zAccount=zAccount)
        else:
            zShippingContact = None

        # Create Payment Method on Account
        if payment_method_id:
            zPaymentMethod = self.get_payment_method(payment_method_id)
        else:
            zPaymentMethod = None

        # Now Update the Draft Account to be Active
        zAccountUpdate = self.client.factory.create('ns2:Account')
        zAccountUpdate.Id = zAccount.Id
        zAccountUpdate.Status = 'Active'
        zAccountUpdate.BillToId = zContact.Id
        if zShippingContact:
            zAccountUpdate.SoldToId = zShippingContact.Id
        else:    
            zAccountUpdate.SoldToId = zContact.Id
        # If we don't require a payment method, AutoPay must be False
        if payment_method_id:
            zAccountUpdate.DefaultPaymentMethodId = payment_method_id
            zAccountUpdate.AutoPay = True
        else:
            zAccountUpdate.AutoPay = False
        response = self.update(zAccountUpdate)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error updating Account. %s" % response)

        return {'account': zAccount, 'contact': zContact,
                'payment_method': zPaymentMethod,
                'shipping_contact': zShippingContact}

    def get_account(self, user_id):
        """
        Checks to see if the loaded user has an account
        """
        qs = """
            SELECT Id FROM Account
            WHERE AccountNumber = '%s' or AccountNumber = 'A-%s'
            """ % (user_id, user_id)

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zAccount = response.records[0]
            return zAccount
        else:
            raise DoesNotExist("Unable to find Account for User ID %s"\
                            % user_id)

    def get_contact(self, email=None, account_id=None):
        """
        Checks to see if the loaded user has a contact
        """
        qs_filter = []

        if account_id:
            qs_filter.append("AccountId = '%s'" % account_id)

        if email:
            qs_filter.append("PersonalEmail = '%s'" % email)

        qs = """
            SELECT
                AccountId, Address1, Address2, City, Country, County,
                CreatedById, CreatedDate, Description, Fax, FirstName,
                HomePhone, Id, LastName, MobilePhone, NickName, OtherPhone,
                OtherPhoneType, PersonalEmail, PostalCode, State, TaxRegion,
                UpdatedById, UpdatedDate, WorkEmail, WorkPhone
            FROM Contact
            WHERE %s
            """  % " AND ".join(qs_filter)

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zContact = response.records[0]
            return zContact
        else:
            raise DoesNotExist("Unable to find Contact for Email %s"\
                            % email)

    def get_invoice(self, invoice_id=None):
        """
        Gets the Invoice
        """

        # Search for Matching Account
        qs = """
            SELECT
                AccountID, AdjustmentAmount, Amount, AmountWithoutTax,
                Balance, CreatedDate, DueDate,
                IncludesOneTime, IncludesRecurring, IncludesUsage,
                InvoiceDate, InvoiceNumber,
                PaymentAmount, RefundAmount, Source, Status,
                TargetDate, TaxAmount, TaxExemptAmount
            FROM Invoice
            WHERE Id = '%s'
            """ % invoice_id

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zInvoice = response.records[0]
            return zInvoice
        else:
            raise DoesNotExist("Unable to find Invoice for Id %s"\
                            % invoice_id)

    def get_invoice_pdf(self, invoice_id=None):
        """
        Gets the Invoice PDF (Base64 Encoded String)
        See: http://bit.ly/Pr7sgT
        """

        # Search for Matching Invoice PDF
        qs = """
            SELECT
                Body
            FROM Invoice
            WHERE Id = '%s'
            """ % invoice_id

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zInvoice = response.records[0]
            return zInvoice.Body
        else:
            raise DoesNotExist("Unable to find Invoice for Id %s"\
                            % invoice_id)

    def get_invoices(self, account_id=None):
        """
        Gets the Invoices matching criteria.

        :param str account_id: Account ID
        """

        # Defaults
        qs_filter = []

        if account_id:
            qs_filter.append("AccountId = '%s'" % account_id)

        if qs_filter:
            qs = """
                SELECT
                    AccountID, AdjustmentAmount, Amount, AmountWithoutTax,
                    Balance, CreatedDate, DueDate,
                    IncludesOneTime, IncludesRecurring, IncludesUsage,
                    InvoiceDate, InvoiceNumber,
                    PaymentAmount, RefundAmount, Source, Status,
                    TargetDate, TaxAmount, TaxExemptAmount
                FROM Invoice
                WHERE %s
                """ % " AND ".join(qs_filter)

            response = self.query(qs)
            zInvoices = response.records

            # Return the Match
            return zInvoices

        # Return None if Not Found
        return None

    def get_invoice_items(self, invoice_id=None, subscription_id=None):
        """
        Gets the InvoiceItems matching criteria.

        :param str invoice_id: Invoice ID
        :param str subscription_id: Subscription ID
        """

        # Defaults
        qs_filter = []

        if invoice_id:
            qs_filter.append("InvoiceId = '%s'" % invoice_id)

        if subscription_id:
            qs_filter.append("SubscriptionId = '%s'" % subscription_id)

        if qs_filter:
            qs = """
                SELECT
                    AccountingCode, ChargeAmount, ChargeDate,
                    ChargeDescription, ChargeName, ChargeNumber,
                    CreatedById, CreatedDate, InvoiceId,
                    ProcessingType, ProductDescription, ProductId,
                    ProductName, Quantity, RatePlanChargeId,
                    RevRecCode, RevRecStartDate, RevRecTriggerCondition,
                    ServiceEndDate, ServiceStartDate, SKU,
                    SubscriptionId, SubscriptionNumber,
                    TaxAmount, TaxCode, TaxExemptAmount, UnitPrice, UOM,
                    UpdatedById, UpdatedDate
                FROM InvoiceItem
                WHERE %s
                """ % " AND ".join(qs_filter)

            response = self.query(qs)
            zRecords = response.records

            # Return the Match
            return zRecords

        # Return None if Not Found
        return None

    def get_invoice_payment(self, invoice_payment_id=None):
        """
        Gets the Invoice Payment

        :param str invoice_payment_id: Invoice Payment ID
        """

        # Search for Matching Account
        qs = """
            SELECT
                Amount, CreatedById, CreatedDate, InvoiceId, PaymentId,
                RefundAmount, UpdatedById, UpdatedDate
            FROM InvoicePayment
            WHERE Id = '%s'
            """ % invoice_payment_id

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zInvoicePayment = response.records[0]
            return zInvoicePayment
        else:
            raise DoesNotExist("Unable to find InvoicePayment for Id %s"\
                            % invoice_payment_id)

    def get_invoice_payments(self, invoice_id=None, payment_id=None):
        """
        Gets the InvoicePayments matching criteria.

        :param str invoice_id: Invoice ID
        :param str payment_id: Payment ID
        """

        # Defaults
        qs_filter = []

        if invoice_id:
            qs_filter.append("InvoiceId = '%s'" % invoice_id)

        if payment_id:
            qs_filter.append("PaymentId = '%s'" % payment_id)

        if qs_filter:
            qs = """
                SELECT
                    Amount, CreatedById, CreatedDate, InvoiceId, PaymentId,
                    RefundAmount, UpdatedById, UpdatedDate
                FROM InvoicePayment
                WHERE %s
                """ % " AND ".join(qs_filter)

            response = self.query(qs)
            zInvoicePayments = response.records

            # Return the Match
            return zInvoicePayments

        # Return None if Not Found
        return None

    def get_payment(self, payment_id=None):
        """
        Gets the zPayment
        """

        # Search for Matching zPayment
        qs = """
            SELECT
                AccountID, AccountingCode, Amount, AppliedCreditBalanceAmount,
                AuthTransactionId,
                BankIdentificationNumber, CancelledOn, Comment,
                CreatedById, CreatedDate, EffectiveDate, GatewayOrderId,
                GatewayResponse, GatewayResponseCode, GatewayState,
                MarkedForSubmissionOn,
                PaymentMethodID, PaymentNumber, ReferenceId, RefundAmount,
                SecondPaymentReferenceId, SettledOn, SoftDescriptor,
                Status, SubmittedOn, TransferredToAccounting,
                Type, UpdatedById, UpdatedDate
            FROM Payment
            WHERE Id = '%s'
            """ % payment_id

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zPayment = response.records[0]
            return zPayment
        else:
            raise DoesNotExist("Unable to find Payment for Id %s"\
                            % payment_id)

    def get_payments(self, account_id=None):
        """
        Gets the Payments matching criteria.

        :param str account_id: Account ID
        """

        # Defaults
        qs_filter = []

        if account_id:
            qs_filter.append("AccountId = '%s'" % account_id)

        if qs_filter:
            qs = """
                SELECT
                    AccountID, AccountingCode, Amount,
                    AppliedCreditBalanceAmount, AuthTransactionId,
                    BankIdentificationNumber, CancelledOn, Comment,
                    CreatedById, CreatedDate, EffectiveDate, GatewayOrderId,
                    GatewayResponse, GatewayResponseCode, GatewayState,
                    MarkedForSubmissionOn,
                    PaymentMethodID, PaymentNumber, ReferenceId, RefundAmount,
                    SecondPaymentReferenceId, SettledOn, SoftDescriptor,
                    Status, SubmittedOn, TransferredToAccounting,
                    Type, UpdatedById, UpdatedDate
                FROM Payment
                WHERE %s
                """ % " AND ".join(qs_filter)

            response = self.query(qs)
            zPayments = response.records

            # Return the Match
            return zPayments

        # Return None if Not Found
        return None

    def get_payment_method(self, payment_method_id):
        """
        Gets the Payment Method details.

        :param str payment_method_id: PaymentMethodId
        """
        qs = """
            SELECT
                AccountId, Active,
                CreatedById, CreatedDate,
                CreditCardAddress1, CreditCardAddress2,
                CreditCardCity, CreditCardCountry,
                CreditCardExpirationMonth, CreditCardExpirationYear,
                CreditCardHolderName, CreditCardMaskNumber,
                CreditCardPostalCode, CreditCardState, CreditCardType,
                Email, Name, PaypalBaid, PaypalEmail,
                PaypalPreapprovalKey, PaypalType, Phone, Type
            FROM PaymentMethod
            WHERE Id = '%s'
            """ % payment_method_id

        response = self.query(qs)
        if getattr(response, "records") and len(response.records) > 0:
            zPaymentMethod = response.records[0]
            return zPaymentMethod
        else:
            raise DoesNotExist("Unable to find Payment Method for %s. %s"\
                            % (payment_method_id, response))

    def get_payment_methods(self, account_id=None, account_number=None,
                            email=None, phone=None):
        """
        Gets the Payment Methods matching criteria.

        :optparam str account_number: Account Number to return the default
            payment method
        :optparam str account_id: Account ID
        :optparam str email: Email Address of the Payee
        :optparam str phone: Phone Number of the Payee
        """

        # Defaults
        qs_filter = []

        # Account Number
        if account_number:
            qs = """
                SELECT
                    DefaultPaymentMethodId
                FROM Account
                WHERE AccountNumber = '%s'
                """ % account_number

            response = self.query(qs)
            if getattr(response, "records") and len(response.records) > 0:
                zAccount = response.records[0]
                # Check for a default payment method
                try:
                    payment_method_id = zAccount.DefaultPaymentMethodId
                except:
                    return None

                # Return as a List
                return [self.get_payment_method(payment_method_id)]

        if account_id:
            qs_filter.append("AccountId = '%s'" % account_id)

        if email:
            qs_filter.append("Email = '%s'" % email)

        if phone:
            qs_filter.append("Phone = '%s'" % phone)

        if qs_filter:
            qs = """
                SELECT
                    AccountId, Active,
                    CreatedById, CreatedDate,
                    CreditCardAddress1, CreditCardAddress2,
                    CreditCardCity, CreditCardCountry,
                    CreditCardExpirationMonth, CreditCardExpirationYear,
                    CreditCardHolderName, CreditCardMaskNumber,
                    CreditCardPostalCode, CreditCardState, CreditCardType,
                    Email, Name, PaypalBaid, PaypalEmail,
                    PaypalPreapprovalKey, PaypalType, Phone, Type
                FROM PaymentMethod
                WHERE %s
                """ % " AND ".join(qs_filter)

            response = self.query(qs)
            zPaymentMethods = response.records

            # Return the Match
            return zPaymentMethods

        # Return None if Not Found
        return None

    def get_products(self, product_id=None, shortcodes=None):
        """
        Gets the Product.

        :param str product_id: ProductID
        :param list shortcodes: List of shortcode strings
        """
        qs_filter = None

        qs = """
            SELECT
                Description, EffectiveEndDate, EffectiveStartDate,
                Id, SKU, Name, ShortCode__c
            FROM Product
            """

        # If we're looking for one specific product
        if product_id:
            qs_filter = "Id = '%s'" % product_id
        # If we're pulling multiple products by their shortcodes
        elif shortcodes:
            qs_filter_list = ["ShortCode__c = '%s'" % code
                                for code in shortcodes]
            qs_filter = " OR ".join(qs_filter_list)

        if qs_filter:
            qs += " WHERE %s" % qs_filter

        response = self.query(qs)
        try:
            zProducts = response.records
            return zProducts
        except:
            raise DoesNotExist("Unable to find Product for %s"\
                            % product_id)

    def get_rate_plan_charges(self, rate_plan_id=None,
                                    rate_plan_id_list=None,
                                    pricing_info="Price"):
        """
        Gets the Rate Plan Charges

        :param str rate_plan_id: RatePlanID
        :param list rate_plan_id_list: list of RatePlanID's
        """
        # Note: Can only use OveragePrice or Price or IncludedUnits or
        # DiscountAmount or DiscountPercentage in one query
        # Note: No clue what that means, but that's the error I get from Zuora
        # if I try to include them all.
        qs = """
            SELECT
                AccountingCode, ApplyDiscountTo,
                BillCycleDay, BillCycleType,
                BillingPeriodAlignment, ChargedThroughDate,
                ChargeModel, ChargeNumber, ChargeType, CreatedById,
                CreatedDate, Description, DiscountLevel,
                DMRC, DTCV, EffectiveEndDate, EffectiveStartDate,
                IsLastSegment, MRR, Name, NumberOfPeriods,
                OriginalId, OverageCalculationOption,
                OverageUnusedUnitsCreditOption, %s,
                PriceIncreasePercentage, ProcessedThroughDate,
                ProductRatePlanChargeId, Quantity, RatePlanId,
                Segment, TCV, TriggerDate, TriggerEvent,
                UnusedUnitsCreditRates, UOM, UpdatedById, UpdatedDate,
                UpToPeriods, UsageRecordRatingOption,
                UseDiscountSpecificAccountingCode, Version
            FROM RatePlanCharge
            """ % pricing_info
        where_id_string = "RatePlanId = '%s'"
        # If only querying with one rate plan id
        if rate_plan_id:
            qs_filter = where_id_string % rate_plan_id
        # Otherwise we're querying with multiple rate plan id's
        else:
            qs_filter = None
            if rate_plan_id_list:
                id_filter_list = [where_id_string % rp_id \
                          for rp_id in rate_plan_id_list]
                # Combine the rate plan ids for the WHERE clause
                qs_filter = " OR ".join(id_filter_list)

        qs += " WHERE %s" % qs_filter

        response = self.query(qs)
        try:
            return response.records
        except:
            raise DoesNotExist(
                            "Unable to find Rate Plan Charges for %s"\
                            % rate_plan_id)

    def get_product_rate_plans(self, product_rate_plan_id=None,
                               product_id_list=None, effective_start=None,
                               effective_end=None):
        """
        Gets the Product Rate Plan.

        :param str product_rate_plan_id: ProductRatePlanID
        :param list prp_id_list: A list of ProductRatePlanID's
        :param datetime effective_start: Effective start date
        :param datetime effective_end: Effective end date
        """
        qs = """
            SELECT
                ActivityLevel__c, AgeGroup__c,
                Description, EffectiveEndDate, EffectiveStartDate,
                Gender__c, Id, Name,
                Priority__c, ProductId, Site__c, Term__c
            FROM ProductRatePlan
            """

        # If only one product is requested
        if product_rate_plan_id:
            qs_filter = "Id = '%s'" % product_rate_plan_id
        # Otherwise multiple products are being requested
        else:
            qs_filter = None
            if product_id_list:
                id_filter_list = ["ProductId = '%s'" % pid \
                          for pid in product_id_list]
                # Combine the product rate plan ids for the WHERE clause
                qs_filter = " OR ".join(id_filter_list)

            if effective_start:
                # If there is an effective start, and not an effective end
                # use the same date for both
                if not effective_end:
                    effective_end = effective_start
                date_where = """EffectiveEndDate >= '%s' AND
                                EffectiveStartDate <= '%s'
                             """ % (effective_end, effective_start)
                # If a previous filter exists, AND them together
                if qs_filter:
                    qs_filter += " AND %s" % date_where
                else:
                    qs_filter = date_where

        qs += " WHERE %s" % qs_filter

        response = self.query(qs)
        try:
            zProductRatePlans = response.records
            return zProductRatePlans
        except:
            raise DoesNotExist("Unable to find Product Rate Plan for %s"\
                            % product_rate_plan_id)

    def get_product_rate_plan_charges(self, product_rate_plan_id=None,
                                      product_rate_plan_id_list=None,
                                      product_rate_plan_charge_id=None):
        """
        Gets the Product Rate Plan Charges.

        :param str product_rate_plan_id: ProductRatePlanID
        :param list product_rate_plan_id_list: list of ProductRatePlanID's
        """
        # Get Product Rate Plan Charges
        qs = """
            SELECT
                AccountingCode, BillCycleDay, BillCycleType, BillingPeriod,
                BillingPeriodAlignment, ChargeModel, ChargeType,
                CustomImageURL__c, DefaultQuantity, Description,
                ExclusiveOfferFlag__c,
                HiddenBenefitText__c, Id,  IncludedUnits, MaxQuantity,
                MinQuantity, Name, NumberOfPeriod, OverageCalculationOption,
                OverageUnusedUnitsCreditOption, PriceIncreaseOption,
                PriceIncreasePercentage, ProductRatePlanId,
                RevRecCode, RevRecTriggerCondition, ShortCode__c,
                SmoothingModel, SortOrder__c, SpecificBillingPeriod,
                TriggerEvent, UOM, UseDiscountSpecificAccountingCode
            FROM ProductRatePlanCharge
            """
        where_id_string = "ProductRatePlanId = '%s'"
        # If only querying with one product rate plan id
        if product_rate_plan_id:
            qs_filter = where_id_string % product_rate_plan_id
        # if we are pulling a product rate plan charge based on its id
        elif product_rate_plan_charge_id:
            qs_filter = "Id = '%s'" % product_rate_plan_charge_id
        # Otherwise multiple products are being requested
        else:
            qs_filter = None
            if product_rate_plan_id_list:
                id_filter_list = [where_id_string % prp_id \
                          for prp_id in product_rate_plan_id_list]
                # Combine the product rate plan ids for the WHERE clause
                qs_filter = " OR ".join(id_filter_list)

        qs += " WHERE %s" % qs_filter

        response = self.query(qs)
        try:
            return response.records
        except:
            raise DoesNotExist(
                            "Unable to find Product Rate Plan Charges for %s"\
                            % product_rate_plan_id)

    def get_product_rate_plan_charge_tiers(
                                    self,
                                    product_rate_plan_charge_id=None,
                                    product_rate_plan_charge_id_list=None):
        """
        Gets the Product Rate Plan Charges.

        :param str product_rate_plan_charge_id: ProductRatePlanChargeId
        :param list product_rate_plan_charge_id_list: list of
                ProductRatePlanChargeId's
        """
        qs = """
            SELECT
                Active, Currency, EndingUnit, IsOveragePrice,
                Price, PriceFormat, ProductRatePlanChargeId,
                StartingUnit, Tier
            FROM ProductRatePlanChargeTier
            """
        where_id_string = "ProductRatePlanChargeId = '%s'"
        # If only one product is requested
        if product_rate_plan_charge_id:
            qs_filter = where_id_string % product_rate_plan_charge_id
        # Otherwise multiple products are being requested
        else:
            qs_filter = None
            if product_rate_plan_charge_id_list:
                id_filter_list = [where_id_string % prpc_id \
                          for prpc_id in product_rate_plan_charge_id_list]
                # Combine the product rate plan charge ids
                # for the WHERE clause
                qs_filter = " OR ".join(id_filter_list)

        qs += " WHERE %s" % qs_filter

        response = self.query(qs)
        try:
            zProductRatePlanChargeTiers = response.records
            return zProductRatePlanChargeTiers
        except:
            raise DoesNotExist(
                    "Unable to find Product Rate Plan Charges Tiers for %s"\
                    % product_rate_plan_charge_id)

    def get_camel_converted_products(self, product_id=None, shortcodes=None):
        """
        Converts a product query response into a camel case
        dictionary of products
        """
        response = self.get_products(product_id=product_id,
                                         shortcodes=shortcodes)

        product_dict = {}
        for p in response:
            product_dict[p.Id] = {}
            for attr in p:
                key = convert_camel(attr[0].replace("__c", ""))
                product_dict[p.Id][key] = attr[1]
        return product_dict

    def get_camel_converted_product_rate_plans(self,
                                               product_rate_plan_id=None,
                                               product_id_list=None,
                                               effective_start=None,
                                               effective_end=None):
        """
        Converts a product rate plan query response into a camel case
        dictionary of product rate plans
        """
        # Get Product and optionally filter by ShortCode
        response = self.get_product_rate_plans(
                                    product_rate_plan_id=product_rate_plan_id,
                                    product_id_list=product_id_list,
                                    effective_start=effective_start,
                                    effective_end=effective_end)

        product_rate_plan_dict = {}
        for rp in response:
            # If there is more than one product and rate plan
            if not product_rate_plan_id:
                product_rate_plan_dict[rp.ProductId] = \
                        product_rate_plan_dict.get(rp.ProductId, {})
                product_rate_plan_dict[rp.ProductId][rp.Id] = {}
            for attr in rp:
                key = convert_camel(attr[0].replace("__c", ""))
                # If there is only one product/rate plan
                if product_rate_plan_id:
                    product_rate_plan_dict[key] = str(attr[1])
                # There are potentially multiple products/rate plans
                else:
                    product_rate_plan_dict[rp.ProductId][rp.Id][key] = \
                                                            str(attr[1])
        return product_rate_plan_dict

    def get_camel_converted_product_rate_plan_charges(
                                            self,
                                            product_rate_plan_id=None,
                                            product_rate_plan_id_list=None):
        """
        Converts a product rate plan charge query response into a camel case
        dictionary of product rate plan charges
        """
        # Get Product and optionally filter by ShortCode
        response = self.get_product_rate_plan_charges(
                        product_rate_plan_id=product_rate_plan_id,
                        product_rate_plan_id_list=product_rate_plan_id_list)

        product_rate_plan_charge_dict = {}
        for rpc in response:
            product_rate_plan_charge_dict[rpc.ProductRatePlanId] = \
                product_rate_plan_charge_dict.get(rpc.ProductRatePlanId, {})

            product_rate_plan_charge_dict[rpc.ProductRatePlanId][rpc.Id] = {}
            for attr in rpc:
                key = convert_camel(attr[0].replace("__c", ""))
                product_rate_plan_charge_dict[\
                            rpc.ProductRatePlanId][rpc.Id][key] = str(attr[1])
        return product_rate_plan_charge_dict

    def get_camel_converted_product_rate_plan_charge_tiers(
                                    self,
                                    product_rate_plan_charge_id_list=None):
        """
        Converts a product rate plan charge tier query response into a
        camel case dictionary of product rate plan charge tiers
        """
        # Get Product and optionally filter by ShortCode
        response = self.get_product_rate_plan_charge_tiers(
                                            product_rate_plan_charge_id_list=\
                                            product_rate_plan_charge_id_list)

        product_rate_plan_charge_tier_dict = {}
        for rpct in response:

            product_rate_plan_charge_tier_dict[rpct.ProductRatePlanChargeId] =\
                product_rate_plan_charge_tier_dict.get(
                                rpct.ProductRatePlanChargeId, {})

            product_rate_plan_charge_tier_dict[\
                                rpct.ProductRatePlanChargeId][rpct.Id] = {}
            for attr in rpct:
                key = convert_camel(attr[0].replace("__c", ""))
                product_rate_plan_charge_tier_dict[\
                    rpct.ProductRatePlanChargeId][rpct.Id][key] = str(attr[1])
        return product_rate_plan_charge_tier_dict

    def match_product_rate_plans(self, shortcodes=[], filter_={}):
        """
        Get matching rate plans based on the product list filter.  This method
        will get all rate plans matching products matching the short codes
        in `product_list`.  It will then return a dictionary of rate plans and
        rate plan charges where each rate plan is the highest scoring rate plan
        per unique product and term.

        TODO: Investigate pre-caching to preload entire rate plan system then
        use this method to match and score out of the cached master.

        TODO: Investigate mem-cache into suez (JK: add memcache capability)

        The filter can have the following keys:
            site, gender, age_group, activity_level

        :param list shortcodes: list of short codes to filter the products
        :param dict filter: dictionary of filters to try to match the best
            rate plan against

        :return: dictionary of rate plans and their rate plan charges
        :rtype: dict
        """

        # Defaults
        matching_rate_plans = []
        qs_datetime_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S')

        # Get Product and optionally filter by ShortCode
        product_dict = self.get_camel_converted_products(shortcodes=shortcodes)

        product_rate_plan_dict = self.get_camel_converted_product_rate_plans(
                                        product_id_list=product_dict.keys(),
                                        effective_start=qs_datetime_now)

        prp_id_list = []
        # Get all of the product rate plan keys for each product
        for product_id, prp_dict in product_rate_plan_dict.items():
            prp_id_list += prp_dict.keys()

        product_rate_plan_charge_dict = \
                self.get_camel_converted_product_rate_plan_charges(
                                        product_rate_plan_id_list=prp_id_list)

        prpc_id_list = []
        # Get all of the product rate plan charge keys
        # for each product rate plan
        for prp_id, prpc_dict in product_rate_plan_charge_dict.items():
            prpc_id_list += prpc_dict.keys()

        product_rate_plan_charge_tier_dict = \
                    self.get_camel_converted_product_rate_plan_charge_tiers(
                                product_rate_plan_charge_id_list=prpc_id_list)

        # Combine Dictionaries
        for product_id, p_dict in product_dict.items():

            # iterate through rate plans
            rp_list = []
            for rate_plan_id, rp_dict in product_rate_plan_dict\
                                            .get(product_id, {}).items():

                # Scoring for Match: Simple increment if regexp matches
                # ie., if filter = {'site': 'mapmyrun.com'} it will score +1
                # if the custom field RatePlan.Site = 'run' or '(run|ride)'
                priority = rp_dict.get("priority", 0)
                rp_dict["score"] = priority
                if filter_:
                    for field, match in filter_.items():
                        if rp_dict.get(field):
                            p = re.compile(rp_dict[field], re.IGNORECASE)
                            if re.match(p, match):
                                rp_dict["score"] += 1

                # iterate through rate plan charges
                rpc_list = []
                for _, rpc_dict in product_rate_plan_charge_dict\
                                            .get(rate_plan_id, {}).items():

                    # get rate plan charge tiers
                    rpct_list = []
                    for (_, rpct_dict) in product_rate_plan_charge_tier_dict\
                                .get(rpc_dict["id"]).items():
                        rpct_list.append(rpct_dict)

                    # append rate plan charge tiers
                    rpc_dict["rate_plan_charge_tiers"] = rpct_list
                    rpc_list.append(rpc_dict)

                # append to rate plan dict after sorting by 'sort_order'
                rp_dict["rate_plan_charges"] = \
                    sorted(rpc_list, key=lambda k: k.get('sort_order', 999))

                # append to rp_list
                rp_list.append(rp_dict)

            # Add to Product Dict but sort by score first
            # TODO: only select highest scoring rate plan per unique term
            p_dict["rate_plans"] = sorted(rp_list,
                                          key=lambda k: k.get('score', 0),
                                          reverse=True)

            matching_rate_plans.append(p_dict)

        # Return Product Rate Plans
        return matching_rate_plans

    def get_product_rate_plan_charge_pricing(self, product_rate_plan_id):
        """
        Gets the Product Rate Plan Charges.
        Sums up the Product Rate Plan Charge Tiers

        :param str product_rate_plan_id: ProductRatePlanID
        """

        products_rate_plan_charge_dict = \
                self.get_camel_converted_product_rate_plan_charges(
                            product_rate_plan_id=product_rate_plan_id)

        # Get the rate plan charges for this specific rate plan
        product_rate_plan_charge_dict = \
                        products_rate_plan_charge_dict[product_rate_plan_id]

        product_rate_plan_charges_tier_dict = \
                    self.get_camel_converted_product_rate_plan_charge_tiers(
                                    product_rate_plan_charge_id_list=\
                                    product_rate_plan_charge_dict.keys())

        # Create the list of rate plan charge tiers
        # within the rate plan charge dict
        for rpc_id, rpct_dict in product_rate_plan_charges_tier_dict.items():
            rate_charge_tiers = product_rate_plan_charge_dict[rpc_id]\
                                .get("rate_charge_tiers", [])
            rate_charge_tiers += rpct_dict.values()
            product_rate_plan_charge_dict[rpc_id]["rate_charge_tiers"] =\
                                                        rate_charge_tiers

        # Run Aggregates
        pricing_dict = {}

        for _, rpc in product_rate_plan_charge_dict.items():
            charge_model = rpc["charge_model"].lower()
            charge_type = rpc["charge_type"].lower()
            pricing_dict[charge_model] = pricing_dict.get(charge_model, {})
            pricing_dict[charge_model][charge_type]\
                = pricing_dict[charge_model].get(charge_type, 0)

            # Iterate through Rate Plan Charge Tiers
            price = pricing_dict[charge_model][charge_type]
            for rpct in rpc["rate_charge_tiers"]:
                is_active = rpct["active"]
                is_overage_price = rpct["is_overage_price"]
                if is_active == True and is_overage_price == False:
                    price = price + float(rpct["price"])

            pricing_dict[charge_model][charge_type] = price

        # Run Aggregates
        return pricing_dict

    def get_rate_plans(self, product_rate_plan_id=None, subscription_id=None):
        """
        Gets the RatePlan matching criteria.

        :optparam str product_rate_plan_id: Product Rate Plan ID
        :optparam str subscription_id: Subscription ID
        """

        # Defaults
        qs_filter = []

        if product_rate_plan_id:
            qs_filter.append("ProductRatePlanId = '%s'" % product_rate_plan_id)

        if subscription_id:
            qs_filter.append("SubscriptionId = '%s'" % subscription_id)

        # Build Query
        qs = """
            SELECT
                AmendmentId, AmendmentSubscriptionRatePlanId,
                AmendmentType, CreatedById, CreatedDate, Name,
                ProductRatePlanId, SubscriptionId,
                UpdatedById, UpdatedDate
            FROM RatePlan
            """

        if qs_filter:
            qs += "WHERE %s" % " AND ".join(qs_filter)

        response = self.query(qs)
        zRecords = response.records

        # Return the Match
        return zRecords

    def get_subscriptions(self, subscription_id=None, account_id=None,
                          auto_renew=None, status=None, term_type=None,
                          term_end_date=None, term_start_date=None,
                          subscription_number=None):
        """
        Gets the Subscriptions matching criteria.

        :optparam str subscription_id: Subscription ID
        :optparam str subscription_number: Unique Subscription number
        :optparam str account_id: Account ID
        :optparam bool auto_renew: AutoRenew (True, False)
        :optparam str status: Subscription Status. Allowable values: Draft,
            Pending Activation, Pending Acceptance, Active, Cancelled, Expired
        :optparam str term_type: Allowable values: EVERGREEN, TERMED
        :optparam date term_end_date: This is when the subscription term ends
        :optparam date term_start_date: The date on which the sub term begins
        """

        # Defaults
        qs_filter = []

        if subscription_id:
            qs_filter.append("Id = '%s'" % subscription_id)

        if subscription_number:
            qs_filter.append("Name = '%s'" % subscription_number)

        if account_id:
            qs_filter.append("AccountId = '%s'" % account_id)

        if auto_renew:
            qs_filter.append("AutoRenew = " + ("'%s'" % auto_renew).lower())

        if status:
            qs_filter.append("Status = '%s'" % status)

        if term_type:
            qs_filter.append("TermType = '%s'" % term_type)

        if term_end_date:
            qs_filter.append("TermEndDate = '%s'" % term_end_date)

        if term_start_date:
            qs_filter.append("TermStartDate = '%s'" % term_start_date)

        # Build Query
        qs = """
            SELECT
                AccountId, AutoRenew,
                CancelledDate, ContractAcceptanceDate,
                ContractEffectiveDate,
                CreatedById, CreatedDate, InitialTerm,
                IsInvoiceSeparate, Name, Notes, OriginalCreatedDate,
                OriginalId, PreviousSubscriptionId,
                RenewalTerm, ServiceActivationDate, Status,
                SubscriptionEndDate, SubscriptionStartDate,
                TermEndDate, TermStartDate, TermType,
                UpdatedById, UpdatedDate, Version
            FROM Subscription
            """

        if qs_filter:
            qs += "WHERE %s" % " AND ".join(qs_filter)

        response = self.query(qs)
        zRecords = response.records

        # Return the Match
        return zRecords

    def make_account(self, user=None, currency='USD', status="Draft",
		     lazy=False, site_name=None):
        """
        The customer's account. Zuora uses the Account object to track all
        subscriptions, usage, and transactions for a single account to be
        billed. Each account is the source of a recurring invoice stream.
        Each account must capture everything Zuora needs in order to bill and
        collect, including "bill to" addresses, payment method and payment
        method details, payment terms (for example, Net 30), and more.
        A new account must be created before a new subscription can be entered.

        :param str currency: currency, defaults to USD
        :param str status: valid values: Draft, Active, (Canceled)

        :returns: zAccount
        """

        # Check User
        if not user:
            raise MissingRequired("No User Selected.")

        # Get Today
        today = date.today()

        # Build Account
        zAccount = self.client.factory.create('ns2:Account')
        zAccount.AccountNumber = "A-%s" % user["id"]
        zAccount.AllowInvoiceEdit = True
        # Zuora requires AutoPay be false at this point. Can be changed later
        zAccount.AutoPay = False
        zAccount.Batch = 'Batch1'
        zAccount.BillCycleDay = today.day
        zAccount.CrmId = str(user["id"])
        zAccount.Currency = currency
        zAccount.Name = "%s, %s"[0:50] % (user["last_name"],
                                          user["first_name"])
        zAccount.PaymentTerm = 'Due Upon Receipt'
        zAccount.Status = status

        # Determine which Payment Gateway to use, if specified
        if self.authorize_gateway:
            zAccount.PaymentGateway = self.authorize_gateway

        if self.create_test_users:
            zAccount.Test_Account__c = 1
            zAccount.User_Site__c = "staging"

        if site_name:
            zAccount.User_Site__c = site_name

        if lazy:
            return zAccount

        response = self.create(zAccount)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error creating Account. %s" % response)
        zAccount.Id = response[0].Id

        # Return
        return zAccount

    def make_contact(self, user=None, billing_address=None, zAccount=None,
                     lazy=False):
        """
        This defines the contact (the end user) for the account. There are two
        types of contacts that need to be created as part of the customer
        account creation: the Bill-To and the Sold-To contacts. Contact
        provides the attributes needed to create these.

        This method creates the contact from the loaded User.

        Uses the billing_address dictionary:
            address1 : str : Address #1
            address2 : str : Address #2
            city : str : City
            country_name : str : Country Name (i.e., United States)
            first_name : str : Person living at Address' First Name
            last_name : str : Person living at Address' Last Name
            postal_code : str : Postal Code
            state : str : Billing Postal Full State Name (i.e., Ohio)

        :returns: zContact
        """

        # Check User / Billing Address
        if not user:
            raise ZuoraException("No User Selected.")

        # Build Contact
        # TODO: remove ns2
        zContact = self.client.factory.create('ns2:Contact')

        if billing_address is not None:
            zContact.FirstName = billing_address["first_name"]
            zContact.LastName = billing_address["last_name"]
            zContact.Address1 = billing_address["street_1"]
            zContact.Address2 = billing_address.get("street_2")
            zContact.City = billing_address["city"]
            zContact.State = billing_address.get("state")
            zContact.PostalCode = billing_address.get("postal_code")
            zContact.Country = billing_address["country_code"]
            if billing_address.get("phone"):
                zContact.HomePhone = billing_address["phone"]
        else:
            zContact.FirstName = user['first_name']
            zContact.LastName = user['last_name']

        zContact.PersonalEmail = user["email"]

        if zAccount is not None and hasattr(zAccount, 'Id'):
            zContact.AccountId = zAccount.Id

        if lazy:
            return zContact

        response = self.create(zContact)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error creating Contact. %s" % response)
        zContact.Id = response[0].Id

        # Return
        return zContact

    def make_rate_plan_data(self, product_rate_plan_id):
        """
        RatePlanData is used to pass complex data to the subscribe() call.
        Each RatePlanData identifies one RatePlan object and a list of one
        or more RatePlanChargeData objects.

        :param str product_rate_plan_id: Product Rate Plan ID

        """

        # Build Rate Plan
        zRatePlan = self.client.factory.create('ns0:RatePlan')
        zRatePlan.AmendmentType = "NewProduct"
        zRatePlan.ProductRatePlanId = product_rate_plan_id

        # Build Rate Plan Data
        zRatePlanData = self.client.factory.create('ns0:RatePlanData')
        zRatePlanData.RatePlan = zRatePlan

        # return Rate Plan Data
        return zRatePlanData

    def make_subscription(self, monthly_term, name=None, notes=None,
                          recurring=True, term_type="TERMED",
                          renewal_term=None, order_id=None,
                          start_date=None):
        """
        This object contains the information needed to create a new
        subscription for the account. It is part of the entire subscribe
        process. The subscribe call is a superset of Subscription.

        A subscription represents a customer signing up for a product for a
        certain amount of time. Each subscription can have one or more
        RatePlans. See Invoking The subscribe() Call for more information
        about creating subscriptions.

        :optparam str name: The name of the subscription. This is a unique\
            identifier. If not specified, Zuora will auto-create a name.
        :param int monthly_term: Term of Subscription (in Months) (12 = 1 Year)
        :optparam str notes: Misc Notes

        :returns: zSubscription
        """

        effective_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        if start_date is None:
            start_date = effective_date

        zSubscription = self.client.factory.create('ns2:Subscription')
        if name:
            zSubscription.Name = name
        if notes:
            zSubscription.Notes = notes

        zSubscription.ContractAcceptanceDate = effective_date
        zSubscription.ContractEffectiveDate = effective_date
        zSubscription.ServiceActivationDate = start_date
        zSubscription.TermStartDate = start_date

        zSubscription.InitialTerm = monthly_term
        # Set RenewalTerm to value explicit value if not None (can be 0)
        if renewal_term is not None:
            zSubscription.RenewalTerm = renewal_term
        # Default to monthly term
        else:
            zSubscription.RenewalTerm = monthly_term
        zSubscription.Status = 'Active'
        zSubscription.AutoRenew = recurring
        zSubscription.TermType = term_type

        # Add Order
        if order_id:
            zSubscription.OrderId__c = order_id

        return zSubscription

    def remove_product_amendment(self, subscription_id, rate_plan_id):
        """
        Use Amendment to make changes to a subscription. For example, if you
        wish to change the terms and conditions of a subscription, you would
        use an Amendment.

        :param str subscription_id: The identification number for the\
            subscription that is being amended.
        :param str rate_plan_id: RatePlanID

        :returns: response
        """
        effective_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        # Create the product amendment removal
        zAmendment = self.create_product_amendment(
                                    effective_date,
                                    subscription_id,
                                    name_prepend="Remove Product Amendment",
                                    amendment_type='RemoveProduct')

        # Make Rate Plan
        zRatePlan = self.client.factory.create('ns0:RatePlan')
        zRatePlan.AmendmentType = "RemoveProduct"
        zRatePlan.AmendmentId = zAmendment.Id
        zRatePlan.AmendmentSubscriptionRatePlanId = rate_plan_id
        response = self.create(zRatePlan)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error creating RatePlan. %s" % response)

        # Update the product amendment
        response = self.update_product_amendment(effective_date, zAmendment)

        return response

    def subscribe(self, product_rate_plan_id, monthly_term, zAccount=None,
                  zContact=None, zShippingContact=None,
                  process_payments_flag=True,
                  generate_invoice_flag=True, generate_preview=False,
                  term_type="TERMED", renewal_term=None,
                  account_name=None, subscription_name=None,
                  recurring=True, payment_method=None, order_id=None,
                  user=None, billing_address=None, shipping_address=None,
                  start_date=None, site_name=None,
                  discount_product_rate_plan_id=None):
        """
        The subscribe() call bundles the information required to create one
        or more new subscriptions. This is a combined call that you can use
        to perform all of the following tasks in a single call.
            - Create accounts
            - Create contacts
            - Create payment methods
            - Apply the first payment to a subscription

        :param str product_rate_plan_id: Product Rate Plan to subscribe to
        :param int monthly_term: Number of Months Subscription Term
        :param bool generate_invoice_flag: Specifies whether an invoice is to\
            be generated when the subscription is created. If a value is not\
            specified, this defaults to true, which gens and posts an invoice.
        :param bool process_payments_flag: Specifies whether payment should\
            be applied when the subscription is created
        :param str account_name: This is the name of the account.
        :param str subscription_name: The name of the subscription. This is a\
            unique identifier. If not specified, Zuora will auto-create a name.
        """
        # zAccount = self.client.factory.create('ns2:Account')
        #Used to be called even if account existed, pulling it out for now
        # Get or Create Account
        if not zAccount:
            zAccount = self.make_account(user=user, site_name=site_name)

        if not zContact and not zAccount.Id:
            # Create Contact
            zContact = self.make_contact(user=user,
                                         billing_address=billing_address,
                                         zAccount=zAccount)
        
        # Add the shipping contact if it exists
        if not zShippingContact and shipping_address:
            zShippingContact = self.make_contact(user=user,
                                         billing_address=shipping_address,
                                         zAccount=zAccount)

        # Get Rate Plan & Build Rate Plan Data
        zRatePlanData = self.make_rate_plan_data(product_rate_plan_id)

        if discount_product_rate_plan_id:
            zDiscountRatePlanData = self.make_rate_plan_data(discount_product_rate_plan_id)
        else:
            zDiscountRatePlanData = None

        # Create Subscription
        zSubscription = self.make_subscription(monthly_term=monthly_term,
                                               recurring=recurring,
                                               order_id=order_id,
                                               start_date=start_date)

        # Attach additional Options
        zSubscriptionOptions = self.client.factory\
                                    .create("ns0:SubscribeOptions")
        zSubscriptionOptions.GenerateInvoice = generate_invoice_flag
        zSubscriptionOptions.ProcessPayments = process_payments_flag

        # Subscription Data
        zSubscriptionData = self.client.factory.create('ns0:SubscriptionData')
        zSubscriptionData.Subscription = zSubscription
        
        # Apply the discount rate plan if it exists
        if zDiscountRatePlanData:
            zSubscriptionData.RatePlanData = [zRatePlanData, zDiscountRatePlanData]
        else:
            zSubscriptionData.RatePlanData = zRatePlanData

        # Subscribe
        zSubscribeRequest = self.client.factory.create('ns0:SubscribeRequest')
        zSubscribeRequest.Account = zAccount
        zSubscribeRequest.BillToContact = zContact
        # Add the shipping contact if it exists
        if zShippingContact:
            zSubscribeRequest.SoldToContact = zShippingContact
        zSubscribeRequest.SubscriptionData = zSubscriptionData
        zSubscribeRequest.SubscribeOptions = zSubscriptionOptions

        zSubscribeRequest.PaymentMethod = payment_method

        # If Preview
        if generate_preview:
            zPreviewOptions = self.client.factory\
                                    .create("ns0:PreviewOptions")
            zPreviewOptions.EnablePreviewMode = True
            zPreviewOptions.NumberOfPeriods = monthly_term + 3
            zSubscribeRequest.PreviewOptions = zPreviewOptions

        fn = self.client.service.subscribe
        response = self.call(fn, zSubscribeRequest)

        # return the response
        return response

    def update_account(self, account_id, update_dict):
        """
        Update a zAccount record

        :param str account_id: ID of the Account
        :param dict update_dict: Dictionary of Property:Value pairs
        """
        # Now Update the Draft Account to be Active
        zAccountUpdate = self.client.factory.create('ns2:Account')
        zAccountUpdate.Id = account_id
        for k, v in update_dict.items():
            setattr(zAccountUpdate, k, v)
        response = self.update(zAccountUpdate)
        if not isinstance(response, list) or not response[0].Success:
            raise ZuoraException(
                "Unknown Error updating Account. %s" % response)


# helper lib
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert_camel(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def zuora_serialize(obj):
    """
    Converts a SUDS Object to a Dictionary
    - Very primative serializer but is able to handle
      the basic Zuora SOAP Objects.
    """
    basic_serializer = [str, int, float, unicode, date, datetime, long]

    if not obj:
        return None

    if isinstance(obj, list):
        obj_list = []
        for item in obj:
            obj_list.append(zuora_serialize(item))
        return obj_list
    else:
        obj_dict = {}
        for attr in obj:
            key = convert_camel(attr[0].replace("__c", ""))

            is_allowed = False
            for allowed in basic_serializer:
                if isinstance(attr[1], allowed):
                    is_allowed = True
            if is_allowed:
                obj_dict[key] = attr[1]
            else:
                obj_dict[key] = zuora_serialize(attr[1])
        return obj_dict

def zuora_serialize_list(response_list):
    """
    Serialize a list of Zuora objects
    """
    serialized_list = []
    if response_list:
        for item in response_list:
            serialized_list.append(zuora_serialize(item))
    return serialized_list
