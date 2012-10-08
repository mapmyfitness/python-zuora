"""
    Unit Tests for Zuora
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import mock

from client import (Zuora, convert_camel, zuora_serialize)

SHORT_CODE_EXAMPLE = 'sub_bronze'


class MockZuoraResponseObject(object):

    def __init__(self):
        self.attributes = [('AutoRenew', True),
                           ('ShortCode__c', SHORT_CODE_EXAMPLE)]

    def __iter__(self):
        for attribute in self.attributes:
            yield attribute


class TestZuora(object):

    def setup_method(self, method):
        self.zuora_settings = {'username': mock.Mock(),
                               'password': mock.Mock(),
                               'wsdl_file': 'zuora.a.39.0.dev.wsdl'}

    def test_create_product_ammendment_create_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.create = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.create.return_value = [response]
        z.create_product_amendment(effective_date=mock.Mock(),
                                subscription_id=mock.Mock(),
                                name_prepend='something',
                                amendment_type=mock.Mock())
        assert z.create.call_count == 1

    def test_update_product_ammendment_update_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.update = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.update.return_value = [response]
        z.update_product_amendment(effective_date=mock.Mock(),
                                zAmendment=mock.Mock())
        assert z.update.call_count == 1

    def test_add_product_ammendment_create_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.create = mock.Mock()
        z.create_product_amendment = mock.Mock()
        z.update_product_amendment = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.create.return_value = [response]
        z.add_product_amendment(name='test',
                                subscription_id=mock.Mock(),
                                product_rate_plan_id=mock.Mock())
        assert z.create_product_amendment.call_count == 1
        assert z.create.call_count == 1

    def test_cancel_subscription_update_called(self):
        z = Zuora(self.zuora_settings)
        z.create_product_amendment = mock.Mock()
        z.update_product_amendment = mock.Mock()
        z.cancel_subscription(subscription_id=mock.Mock())
        assert z.create_product_amendment.call_count == 1
        assert z.update_product_amendment.call_count == 1

    def test_create_active_account_get_payment_method_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.get_payment_method = mock.Mock()
        z.update = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.update.return_value = [response]
        z.create_active_account(zAccount=mock.Mock(), zContact=mock.Mock(),
                                payment_method_id=mock.Mock(),
                                user=None, billing_address=None)
        assert z.get_payment_method.call_count == 1
        assert z.update.call_count == 1

    def test_get_account_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_account(user_id=42)
        assert z.query.call_count == 1

    def test_get_contact_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_contact(email='guy42@gmail.com', account_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoice_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_invoice(invoice_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoice_pdf_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        zInvoice = mock.Mock()
        zInvoice.Body = mock.Mock()
        response.records = [zInvoice]
        z.query.return_value = response
        z.get_invoice_pdf(invoice_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoices_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_invoices(account_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoice_items_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_invoice_items(invoice_id=mock.Mock(),
                            subscription_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoice_payment_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_invoice_payment(invoice_payment_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_invoice_payments_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_invoice_payments(invoice_id=mock.Mock(),
                               payment_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_payment_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_payment(payment_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_payments_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_payments(account_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_payment_method_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_payment_method(payment_method_id=mock.Mock())
        assert z.query.call_count == 1

    def test_get_payment_methods_get_payment_method_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        zAccount = mock.Mock()
        zAccount.DefaultPaymentMethodId = mock.Mock()
        response.records = [zAccount]
        z.query.return_value = response
        z.get_payment_methods(account_number=mock.Mock())
        assert z.query.call_count == 2

    def test_get_payment_methods_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_payment_methods(account_id=mock.Mock(),
                              email='guy42@gmail.com',
                              phone=mock.Mock())
        assert z.query.call_count == 1

    def test_get_products_product_id(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_products(product_id='df2423dffgf')
        assert z.query.call_count == 1

    def test_get_products_shortcodes(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_products(shortcodes=['sub_bronze', 'sub_gold'])
        assert z.query.call_count == 1
    
    def test_get_rate_plan_charges_rate_plan_id(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_rate_plan_charges(rate_plan_id='df2423dffgf')
        assert z.query.call_count == 1
    
    def test_get_product_rate_plans_product_rate_plan_id(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plans(product_rate_plan_id='df2423dffgf')
        assert z.query.call_count == 1

    def test_get_product_rate_plans_product_id_list(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plans(product_id_list=['df2423dffgf',
                                                  'fdsgd234233g'],
                                 effective_start=mock.Mock())
        assert z.query.call_count == 1

    def test_get_product_rate_plan_charges_product_rate_plan_id(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plan_charges(product_rate_plan_id='df2423dffgf')
        assert z.query.call_count == 1

    def test_get_product_rate_plan_charges_product_rate_plan_id_list(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plan_charges(
                                product_rate_plan_id_list=['df2423dffgf',
                                                           'fdsgd234233g'])
        assert z.query.call_count == 1

    def test_get_product_rate_plan_charge_tiers_product_rate_plan_charge_id(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plan_charge_tiers(
                                product_rate_plan_charge_id='df2423dffgf')
        assert z.query.call_count == 1

    def test_get_product_rate_plan_charge_tiers_product_rate_plan_charge_id_list(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_product_rate_plan_charge_tiers(
                        product_rate_plan_charge_id_list=['df2423dffgf',
                                                          'fdsgd234233g'])
        assert z.query.call_count == 1

    def test_match_product_rate_plans(self):
        z = Zuora(self.zuora_settings)
        z.get_camel_converted_products = mock.Mock()
        z.get_camel_converted_product_rate_plans = mock.Mock()
        z.get_camel_converted_product_rate_plan_charges = mock.Mock()
        z.get_camel_converted_product_rate_plan_charge_tiers = mock.Mock()
        z.get_camel_converted_products.return_value = {}
        z.get_camel_converted_product_rate_plans.return_value = {}
        z.get_camel_converted_product_rate_plan_charges.return_value = {}
        z.get_camel_converted_product_rate_plan_charge_tiers.return_value = {}
        z.match_product_rate_plans(shortcodes=['sub_bronze', 'sub_gold'])
        assert z.get_camel_converted_products.call_count == 1
        assert z.get_camel_converted_product_rate_plans.call_count == 1
        assert z.get_camel_converted_product_rate_plan_charges.call_count == 1
        assert z.get_camel_converted_product_rate_plan_charge_tiers.call_count\
                                                                        == 1

    def test_get_product_rate_plan_charge_pricing(self):
        z = Zuora(self.zuora_settings)
        product_rate_plan_id = 'df2423dffgf'
        z.get_camel_converted_product_rate_plan_charges = mock.Mock()
        z.get_camel_converted_product_rate_plan_charge_tiers = mock.Mock()
        z.get_camel_converted_product_rate_plan_charges.return_value = {
                                        product_rate_plan_id: {}}
        z.get_camel_converted_product_rate_plan_charge_tiers.return_value = {}
        z.get_product_rate_plan_charge_pricing(
                                    product_rate_plan_id=product_rate_plan_id)
        assert z.get_camel_converted_product_rate_plan_charges.call_count == 1
        assert z.get_camel_converted_product_rate_plan_charge_tiers.call_count\
                                                                        == 1

    def test_get_rate_plans_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_rate_plans(product_rate_plan_id='df2423dffgf',
                                 subscription_id='df2423dffgf')
        assert z.query.call_count == 1

    def test_get_subscriptions_query_called(self):
        z = Zuora(self.zuora_settings)
        z.query = mock.Mock()
        response = mock.Mock()
        response.records = [1]
        z.query.return_value = response
        z.get_subscriptions(account_id='df2423dffgf',
                            auto_renew='True',
                            status='Good?',
                            term_type='Evergreen',
                            term_end_date=mock.Mock(),
                            term_start_date=mock.Mock())
        assert z.query.call_count == 1

    def test_remove_product_amendment_create_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.create_product_amendment = mock.Mock()
        z.update_product_amendment = mock.Mock()
        z.create_product_amendment.return_value = mock.Mock()
        z.create = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.create.return_value = [response]
        z.remove_product_amendment(subscription_id=mock.Mock(),
                                   rate_plan_id=mock.Mock())
        assert z.create_product_amendment.call_count == 1
        assert z.create.call_count == 1

    def test_subscribe_call_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.make_account = mock.Mock()
        z.make_contact = mock.Mock()
        z.make_rate_plan_data = mock.Mock()
        z.make_subscription = mock.Mock()
        z.call = mock.Mock()
        z.call.return_value = mock.Mock()
        z.subscribe(product_rate_plan_id=mock.Mock(),
                    monthly_term=mock.Mock(),
                    zAccount=None,
                    zContact=None,
                    process_payments_flag=True,
                    generate_invoice_flag=True,
                    generate_preview=False,
                    account_name=mock.Mock(),
                    subscription_name=mock.Mock(),
                    recurring=True,
                    payment_method=mock.Mock(),
                    order_id=mock.Mock(),
                    user=mock.Mock(),
                    billing_address=mock.Mock(),)
        assert z.make_account.call_count == 1
        assert z.make_rate_plan_data.call_count == 1
        assert z.make_subscription.call_count == 1
        assert z.call.call_count == 1

    def test_update_account_update_called(self):
        z = Zuora(self.zuora_settings)
        z.client = mock.Mock()
        z.update = mock.Mock()
        response = mock.Mock()
        response.Success = True
        z.update.return_value = [response]
        z.update_account(account_id=mock.Mock(),
                         update_dict={})
        assert z.update.call_count == 1

    def test_convert_camel(self):
        assert convert_camel("AutoRenew") == "auto_renew"

    def test_zuora_serialize(self):
        obj = MockZuoraResponseObject()
        assert zuora_serialize(obj) == {'auto_renew': True,
                                        'short_code': SHORT_CODE_EXAMPLE}
