import json
import logging
import os
import time

import requests

platform_name = 'rozetka'
url = 'https://search.rozetka.com.ua/ua/search/api/v6/'
params = {'country': 'UA', 'lang': 'ua'}

log_dir = f'platforms/fetched/{platform_name}/'
logger = logging.getLogger(platform_name)


def search_query(query: str, timeout: int = 30, log_queries: bool = False) -> dict:
    logger.info('[ROZETKA] Fetching data from ' + platform_name)
    logger.debug('[ROZETKA] Query: ' + query)

    params['text'] = query
    result_data = {'products': [], 'timestamp': time.time()}
    current_page = 1

    timer = time.time()

    while True:
        logger.debug('[ROZETKA] page: ' + str(current_page))
        params['page'] = current_page

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception('Failed to fetch data:', response.status_code, response.text)

        # Parse the JSON response
        data = response.json()

        # Save the response to a file
        if log_dir and log_queries:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{current_page}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        # Process the JSON data
        data = data['data']
        products = data['goods']
        logger.debug('[ROZETKA] products count: ' + str(len(products)))
        for product in products:
            result_data['products'].append({
                'id': product['id'],
                'name': product['title'],
                'href': product['href'],
                'img_href': product['image_main'],
                'brand': product['brand'],
                'price': product['price'],
                'in_stock': product['status'] and product['status'] == 'available'
            })

        if current_page >= data['pagination']['total_pages']:
            break

        if time.time() - timer >= timeout:
            logger.warning('[ROZETKA] Timeout reached')
            raise Exception('Timeout reached')

        logger.debug('[ROZETKA] fetch page done')
        current_page += 1

    logger.info('[ROZETKA] Fetching data from ' + platform_name + ' done')
    return result_data
