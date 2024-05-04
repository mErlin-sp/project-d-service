import json
import os
import time

import requests

timeout = 30

platform_name = 'rozetka'
url = 'https://search.rozetka.com.ua/ua/search/api/v6/'
params = {'country': 'UA', 'lang': 'ua'}

log_dir = 'platforms/fetched/rozetka/'


def fetch_data(query: str) -> dict:
    print('Fetching data from', platform_name)
    print('Query:', query)

    params['text'] = query
    result_data = {'goods': [], 'timestamp': time.time()}
    current_page = 1

    timer = time.time()

    while True:
        print('page:', current_page)
        params['page'] = current_page

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception('Failed to fetch data:', response.status_code, response.text)

        # Parse the JSON response
        data = response.json()

        # Save the response to a file
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f'{query}-{current_page}-{time.time()}.json'), 'w') as f:
                json.dump(data, f, indent=2)

        # Process the JSON data
        data = data['data']
        goods = data['goods']
        print('goods count:', len(goods))
        for good in goods:
            result_data['goods'].append({
                'id': good['id'],
                'name': good['title'],
                'href': good['href'],
                'img_href': good['image_main'],
                'brand': good['brand'],
                'price': good['price'],
            })

        if current_page >= data['pagination']['total_pages']:
            break

        if time.time() - timer >= timeout:
            print('Timeout reached')
            raise Exception('Timeout reached')

        print('fetch page done')
        current_page += 1

    print('Fetching data from', platform_name, 'done')
    return result_data
