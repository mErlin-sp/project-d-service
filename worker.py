import json
import os
import time
from importlib.util import spec_from_file_location, module_from_spec
from types import ModuleType

from db import DB


def print_platforms(platforms: [(str, ModuleType)]):
    print('Platforms: ', )
    for platform, module in platforms:
        print('    ', platform)
    print('')


def load_platform(platform_dir: str) -> ModuleType:
    try:
        spec = spec_from_file_location(platform_dir[:-3], platform_dir)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        return module
    except Exception as e:
        print('Load platform error:', e)
        raise e


def list_platforms(platforms_dir: str) -> (str, ModuleType):
    platforms = []

    try:
        for platform_file in os.listdir(platforms_dir):
            if platform_file.endswith('.py'):
                try:
                    platform = platform_file[:-3]  # Remove .py extension
                    module = load_platform(os.path.join(platforms_dir, platform_file))

                    if hasattr(module, 'fetch_data') and callable(module.fetch_data):
                        if hasattr(module, 'ready') and not module.ready:
                            print('Platform', platform, 'is not ready')
                            continue

                        platforms.append((platform, module))

                except Exception as e:
                    print('Load platform_file', platform_file, 'error:', e)
                    continue

        print_platforms(platforms)

    except Exception as e:
        print('List platforms error:', e)

    return platforms


def update_db_with_fetch_data(db: DB, data: dict, platform: str, query_id: int):
    print('Updating DB with fetched data...')

    try:
        for good in data['goods']:
            good_id = db.execute_query('SELECT id FROM goods WHERE platform_id = %s AND query_id = %s',
                                       (good['id'], query_id))
            if not good_id:
                print('Inserting good:', good['name'])
                good_id = db.execute_query(
                    'INSERT INTO goods (platform,platform_id, query_id, name, href, img_href, brand) VALUES (%s,%s, '
                    '%s, %s, %s, %s, %s)',
                    (platform, good['id'], query_id, good['name'], good['href'], good['img_href'], good['brand']), True)
            else:
                good_id = good_id[0][0]

            # Add the price to the prices table
            db.execute_query('INSERT INTO prices (good_id, price) VALUES (%s, %s)', (good_id, good['price']))

    except Exception as e:
        print('Update db with fetched data error:', e)

    print('DB updated with fetched data.')


def update_db(db: DB, platforms_dir: str, log_dir: str = None):
    print('Updating DB...')
    print('Current time: ', time.ctime())

    queries = db.get_active_queries()
    print('Active queries: ', queries)

    platforms = list_platforms(platforms_dir)

    for platform, module in platforms:
        for query_id, query in queries:
            try:
                print('Fetching data from', platform, 'for query:', query)
                data = module.fetch_data(query)
                print('Data fetched successfully!')

                update_db_with_fetch_data(db, data, platform, query_id)

                if log_dir:
                    try:
                        path = os.path.join(log_dir, platform)
                        os.makedirs(path, exist_ok=True)
                        with open(os.path.join(path, f'{query}-{time.time()}.json'), 'w') as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        print('Failed to save fetched data:', e)
            except Exception as e:
                print('Fetch data from platform', platform, 'error:', e)

    print('DB updated.')
    print('--' * 50)
    print('')
