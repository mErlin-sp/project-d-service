import json
import os
import time

from gql.transport.requests import RequestsHTTPTransport
from gql import Client, gql

platform_name = 'promua'
url = 'https://prom.ua/graphql'
gql_query_filepath = 'platforms/gql/promua-gql-query.gql'

limit = 95
max_products = None

params = {
    'limit': limit,
    'offset': 0
}

log_dir = 'platforms/fetched/promua/'


def search_query(query: str, timeout: int = 60 * 5) -> dict:
    print('Fetching data from PromUA')
    print('Query:', query)

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
            print('Timeout reached')
            raise Exception('Timeout reached')

        print('offset:', offset)
        params['offset'] = offset

        data = client.execute(gql_query, variable_values=params)
        # print(data)

        # Save the response to a file
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{offset}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        products = data['searchListing']['page']['products']

        if not products:
            break

        print('fetched:', len(products))

        for _ in products:
            product = _['product']

            if max_products and len(result_data['products']) >= max_products:
                print('Max products reached')
                return result_data

            result_data['products'].append({
                'id': product['id'],
                'name': product['name'],
                'href': product['urlForProductViewOnSite'],
                'img_href': product['image'],
                'brand': product['manufacturer'],
                'price': product['price'],
            })

        print('done')
        offset += limit
        time.sleep(3)

    print('Fetching data from', platform_name, 'done')
    return result_data

# print(search_query('Чохол для iPhone 12 Pro Max'))
