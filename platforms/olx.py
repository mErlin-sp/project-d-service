import json
import os
import time

import requests

platform_name = 'olx'
url = 'https://www.olx.ua/api/v1/offers/'

limit = 50
max_products = None

params = {'offset': 0,
          'limit': limit,
          'filter_refiners': 'spell_checker',
          'suggest_filters': 'true'}

log_dir = f'platforms/fetched/{platform_name}/'


def search_query(query: str, timeout: int = 60 * 5, delay: int = 1, logging: bool = False) -> dict:
    print('[OLX] Fetching data from OLX')
    print('[OLX] Query:', query)

    params['query'] = query

    result_data = {'products': [], 'timestamp': time.time()}
    offset = 0

    timer = time.time()

    while True:

        if time.time() - timer >= timeout:
            print('[OLX] Timeout reached')
            raise Exception('Timeout reached')

        print('[OLX] offset:', offset)
        params['offset'] = offset

        response = requests.get(url, params=params)
        if response.status_code != 200:
            if response.json()['error']['title'] == 'Invalid request':
                print('[OLX] Invalid request. Maybe reached the end?')
                return result_data

            raise Exception('Failed to fetch data:', response.status_code, response.text)

        # Parse the JSON response
        data = response.json()

        # Save the response to a file
        if log_dir and logging:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{offset}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        products = data['data']
        # print(products)

        if not products:
            break

        print('[OLX] fetched:', len(products))

        for product in products:
            if max_products and len(result_data['products']) >= max_products:
                print('[OLX] Max products reached')
                return result_data

            product_params = product['params']
            price = None
            try:
                # print('[OLX] params:', product_params)
                price_param_index = next(
                    (i for i, item in enumerate(product_params) if
                     item.get('key') == 'price' and item.get('type') == 'price'), None)
                if price_param_index is not None:
                    price = product_params[price_param_index]['value']['value']
                # print('[OLX] price:', price)
            except Exception as e:
                print('[OLX] Price extraction error:', e)

            result_data['products'].append({
                'id': product['id'],
                'name': product['title'],
                'href': product['url'],
                'img_href': product['photos'][0]['link'] if product['photos'] else None,
                'brand': None,
                'price': price,
                'in_stock': True,
            })

        print('[OLX] done')
        offset += limit
        time.sleep(delay)

    print('[OLX] Fetching data from', platform_name, 'done')
    return result_data

# print(search_query('Чехол Iphone 15'))
