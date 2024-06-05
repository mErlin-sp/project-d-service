import json
import os
import threading
import time
from datetime import datetime, timezone
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

                    if hasattr(module, 'search_query') and callable(module.search_query):
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
    print('Products count:', len(data['products']))

    try:
        for good in data['products']:
            try:
                good_id = db.execute_query(
                    '''SELECT id FROM goods WHERE platform_id = {} AND query_id = '{}' '''.format(good['id'], query_id))

                if not good_id:
                    print('Inserting good:', good['name'])
                    good_id = db.execute_query(
                        '''INSERT INTO goods (platform,platform_id, query_id, name, href, img_href, brand) VALUES (
                        "{}","{}", "{}", "{}", "{}", "{}", "{}")'''.format(platform, good['id'], query_id, good['name'],
                                                                           good['href'],
                                                                           good['img_href'], good['brand']),
                        True)
                else:
                    good_id = good_id[0][0]

                # Add the price to the prices table
                # print('Inserting price', good['price'], 'for good', good['name'])
                if good['price']:
                    db.execute_query(
                        '''INSERT INTO prices (good_id, price) VALUES ('{}', '{}')'''.format(good_id, good['price']))
                # Add the stock status to the in_stock table
                # print('Inserting stock status', good['in_stock'], 'for good', good['name'])
                db.execute_query('''INSERT INTO in_stock (good_id, in_stock) VALUES ('{}', {})'''.format(good_id,
                                                                                                         good[
                                                                                                             'in_stock']))
                # Update the last_confirmed field in the goods table
                db.execute_query('''UPDATE goods SET last_confirmed = '{}' WHERE id = '{}' '''.format(
                    datetime.fromtimestamp(data['timestamp'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    good_id, ))
            except Exception as e:
                print('Insert good error:', e)
                continue

    except Exception as e:
        print('Update db with fetched data error:', e)

    print('DB updated with fetched data.')


def update_platform(platform: str, module: ModuleType, queries: [(int, str)], db: DB, log_dir: str = None):
    print('Updating DB for platform', platform)
    for query_id, query in queries:
        try:
            data = module.search_query(query)
            if log_dir:
                try:
                    path = os.path.join(log_dir, platform)
                    os.makedirs(path, exist_ok=True)
                    with open(os.path.join(path, f'{query}-{time.time()}.json'), 'w') as f:
                        json.dump(data, f, indent=2)
                except Exception as e:
                    print('Failed to save fetched data:', e)

            update_db_with_fetch_data(db, data, platform, query_id)

            print('--' * 50)
            print('')
        except Exception as e:
            print('Update DB for platform', platform, 'query', query, 'error:', e)

    print('DB updated for platform', platform)
    print('--' * 50)
    print('')


def update_db(db: DB, platforms_dir: str, log_dir: str = None):
    print('Updating DB...')
    print('Current time: ', time.ctime())

    queries = db.get_active_queries()
    if queries:
        print('Active queries: ', queries)
    else:
        print('No active queries.')
        print('--' * 50)
        print('')
        return

    platforms = list_platforms(platforms_dir)
    threads = []

    for platform, module in platforms:
        # Create a thread that will run the function
        platform_thread = threading.Thread(target=update_platform, args=(platform, module, queries, db, log_dir))
        # Start the thread
        platform_thread.start()
        # Add the thread to the list
        threads.append(platform_thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print('DB updated.')
    print('--' * 50)
    print('')
