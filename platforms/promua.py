import json
import logging
import os
import time

from gql.transport.requests import RequestsHTTPTransport
from gql import Client, gql

platform_name = 'promua'
url = 'https://prom.ua/graphql'
gql_query_filepath = 'platforms/gql/promua/promua-gql-query.gql'

limit = 95
max_products: int | None = None

params = {
    'limit': limit,
    'offset': 0
}

log_dir = f'platforms/fetched/{platform_name}/'
logger = logging.getLogger(platform_name)


def search_query(query: str, timeout: int = 60 * 5, delay: int = 1, log_queries: bool = False) -> dict:
    logger.info('[PROM.UA] Fetching data from PromUA')
    logger.debug('[PROM.UA] Query: ' + query)

    params['search_term'] = query

    result_data = {'products': [], 'timestamp': time.time()}
    offset = 0

    transport = RequestsHTTPTransport(
        url=url,
        verify=True,
        retries=3,
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    with open(gql_query_filepath, 'r') as file:
        query_str = file.read()

    if not query_str:
        raise Exception('Failed to read the query file')

    gql_query = gql(query_str)

    timer = time.time()

    while True:

        if time.time() - timer >= timeout:
            logger.warning('[PROM.UA] Timeout reached')
            raise Exception('Timeout reached')

        logger.debug('[PROM.UA] offset: ' + str(offset))
        params['offset'] = offset

        data = client.execute(gql_query, variable_values=params)
        # print(data)

        # Save the response to a file
        if log_dir and log_queries:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{offset}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        products = data['searchListing']['page']['products']

        if not products:
            break

        logger.debug('[PROM.UA] fetched: ' + str(len(products)))

        for _ in products:
            product = _['product']

            if max_products and len(result_data['products']) >= max_products:
                logger.warning('[PROM.UA] Max products reached')
                return result_data

            result_data['products'].append({
                'id': product['id'],
                'name': product['name'],
                'href': product['urlForProductViewOnSite'],
                'img_href': product['image'],
                'brand': product['manufacturer'],
                'price': product['price'],
                'in_stock': product['presence'] and product['presence']['isAvailable']
            })

        logger.debug('[PROM.UA] done')
        offset += limit
        time.sleep(delay)

    logger.info('[PROM.UA] Fetching data from ' + platform_name + ' done')
    return result_data

# print(search_query('Чохол для iPhone 12 Pro Max'))
