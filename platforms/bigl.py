import json
import os
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


def search_query(query: str, timeout: int = 60 * 5, delay: int = 1) -> dict:
    print('Fetching data from Bigl')
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
                'href': product['url'],
                'img_href': product['main_image']['url'] if 'main_image' in product else None,
                'brand': product['manufacturerInfo']['name'] if 'manufacturerInfo' in product else None,
                'price': product['price'],
            })

        print('done')
        offset += limit
        time.sleep(delay)

    print('Fetching data from', platform_name, 'done')
    return result_data

# print(search_query('Чохол для iPhone 12 Pro Max'))
