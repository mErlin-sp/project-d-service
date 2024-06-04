import json
import logging
import os
import time

import requests

platform_name = 'olx'
url = 'https://www.olx.ua/api/v1/offers/'

limit = 50
max_products: int | None = None

params = {'offset': 0,
          'limit': limit,
          'filter_refiners': 'spell_checker',
          'suggest_filters': 'true'}

log_dir = f'platforms/fetched/{platform_name}/'
logger = logging.getLogger(platform_name)


def search_query(query: str, timeout: int = 60 * 5, delay: int = 1, log_queries: bool = False) -> dict:
    logger.info('[OLX] Fetching data from OLX')
    logger.debug('[OLX] Query: ' + query)

    params['query'] = query

    result_data = {'products': [], 'timestamp': time.time()}
    offset = 0

    timer = time.time()

    while True:

        if time.time() - timer >= timeout:
            logger.warning('[OLX] Timeout reached')
            raise Exception('Timeout reached')

        logger.debug('[OLX] offset: ' + str(offset))
        params['offset'] = offset

        response = requests.get(url, params=params)
        if response.status_code != 200:
            if response.json()['error']['title'] == 'Invalid request':
                logger.warning('[OLX] Invalid request. Maybe reached the end?')
                return result_data

            raise Exception('Failed to fetch data:', response.status_code, response.text)

        # Parse the JSON response
        data = response.json()

        # Save the response to a file
        if log_dir and log_queries:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{offset}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        products = data['data']

        if not products:
            break

        logger.debug('[OLX] fetched:' + str(len(products)))

        for product in products:
            if max_products and len(result_data['products']) >= max_products:
                logger.warning('[OLX] Max products reached')
                return result_data

            product_params = product['params']
            price = None
            try:
                # logger.debug('[OLX] params:', product_params)
                price_param_index = next(
                    (i for i, item in enumerate(product_params) if
                     item.get('key') == 'price' and item.get('type') == 'price'), None)
                if price_param_index is not None:
                    price = product_params[price_param_index]['value']['value']
                # logger.debug('[OLX] price:', price)
            except Exception as e:
                logger.warning('[OLX] Price extraction error:', e)

            result_data['products'].append({
                'id': product['id'],
                'name': product['title'],
                'href': product['url'],
                'img_href': product['photos'][0]['link'] if product['photos'] else None,
                'brand': None,
                'price': price,
                'in_stock': True,
            })

        logger.debug('[OLX] done')
        offset += limit
        time.sleep(delay)

    logger.info('[OLX] Fetching data from', platform_name, 'done')
    return result_data

# print(search_query('Чехол Iphone 15'))
