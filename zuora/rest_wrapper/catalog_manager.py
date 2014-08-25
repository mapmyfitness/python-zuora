import requests
from request_base import RequestBase, rest_client_reconnect

# For more information on parameters and responses, please see
# http://knowledgecenter.zuora.com/D_Zuora_APIs/REST_API/B_REST_API_reference/Catalog


class CatalogManager(RequestBase):
    
    @rest_client_reconnect
    def get_catalog(self, pageSize=10, page=1):
        fullUrl = self.zuora_config.base_url + 'catalog/products'
        params = {'pageSize': pageSize,
                  'page': page}
    
        response = requests.get(fullUrl, params=params,
                                headers=self.zuora_config.headers,
                                verify=False)
        return self.get_json(response)
