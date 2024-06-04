import json
import logging
import os
import sys
import time

from gql.transport.requests import RequestsHTTPTransport
from gql import Client, gql

platform_name = 'bigl'
url = 'https://bigl.ua/graphql'
gql_query_filepath = 'platforms/gql/bigl/bigl-gql-query.gql'

limit = 95
max_products = 5000

params = {
    'limit': limit,
    'offset': 0
}

log_dir = f'platforms/fetched/{platform_name}/'
logger = logging.getLogger(__name__)


def search_query(query: str, timeout: int = 60 * 5, delay: int = 1, log_queries: bool = False) -> dict:
    logger.info('[BIGL] Fetching data from Bigl')
    logger.debug('[BIGL] Query: ' + query)

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
            logger.warning('[BIGL] Timeout reached')
            raise Exception('Timeout reached')

        logger.debug('[BIGL] offset: ' + str(offset))
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

        logger.debug('[BIGL] fetched: ' + str(len(products)))

        for _ in products:
            product = _['product']

            if max_products and len(result_data['products']) >= max_products:
                logger.warning('[BIGL] Max products reached')
                return result_data

            result_data['products'].append({
                'id': product['id'],
                'name': product['name'],
                'href': product['url'],
                'img_href': product['main_image']['url'] if 'main_image' in product else None,
                'brand': product['manufacturerInfo']['name'] if 'manufacturerInfo' in product else None,
                'price': product['price'],
                'in_stock': product['presence'] and product['presence'] == 'avail'
            })

        logger.debug('[BIGL] done')
        offset += limit
        time.sleep(delay)

    logger.info('[BIGL] Fetching data from ' + platform_name + ' done')
    return result_data

# print(search_query('Чохол для iPhone 12 Pro Max'))
