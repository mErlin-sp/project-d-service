import json
import os
import time

import requests

timeout = 30

url = 'https://search.rozetka.com.ua/ua/search/api/v6/'
params = {'country': 'UA', 'lang': 'ua'}


def fetch_data(query: str):
    print('Fetching data from Rozetka')
    print('Query:', query)

    params['text'] = query
    result_data = {'goods': []}
    current_page = 1

    timer = time.time()

    while True:
        print('Fetching page:', current_page)
        params['page'] = current_page
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception('Failed to fetch data:', response.status_code, response.text)

        # Parse the JSON response
        data = response.json()

        # Save the response to a file
        # os.makedirs('responses/rozetka/', exist_ok=True)
        # with open(f'responses/rozetka/{query}-{current_page}-{time.time()}.json', 'w') as f:
        #     json.dump(data, f, indent=2)
        # print(data)

        # Process the JSON data
        print('goods count:', len(data['data']['goods']))
        for good in data['data']['goods']:
            result_data['goods'].append({
                'id': good['id'],
                'name': good['title'],
                'href': good['href'],
                'img_href': good['image_main'],
                'brand': good['brand'],
                'price': good['price'],
            })

        if current_page >= data['data']['pagination']['total_pages']:
            break

        if time.time() - timer >= timeout:
            print('Timeout reached')
            raise Exception('Timeout reached')

        print('Fetching page done:', current_page)
        current_page += 1

    print('Fetching data from Rozetka done')
    return result_data
