import json
import os
import time
from importlib.util import spec_from_file_location, module_from_spec
from threading import Thread

import schedule
import uvicorn
from fastapi import FastAPI

from db import DB

# DB connection parameters
db_host: str = '127.0.0.1'
db_port: int = 3306
db_user: str = 'root'
db_password: str = 'qwertyuiop'
db_database: str = 'project-d-db'

# Initialize DB
db = DB(db_host, db_port, db_user, db_password, db_database)

# API parameters
api_host: str = '127.0.0.1'
api_port: int = 8000

# Initialize FastAPI
api = FastAPI()

platforms_dir = 'platforms/'


@api.get("/")
async def root():
    return {"message": "Hello World"}


@api.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@api.get("/db/queries")
async def get_queries():
    return {"rows": db.get_queries()}


@api.get("/db/queries/active")
async def get_active_queries():
    return {"rows": db.get_active_queries()}


def run_api():
    uvicorn.run(api, host=api_host, port=api_port)
    print('API is running...')


def init():
    print('project-d service is initializing...')
    db.db_init()
    print('project-d service is initialized.')


def update_db():
    print('Updating DB...')
    print('Current time: ', time.ctime())
    queries = db.get_active_queries()
    print('Active queries: ', queries)

    try:
        # Iterate over files in the platforms directory
        for platform in os.listdir(platforms_dir):
            if platform.endswith('.py'):
                try:
                    platform_py = os.path.join(platforms_dir, platform)
                    module_name = platform_py[:-3]  # Remove .py extension
                    spec = spec_from_file_location(module_name, platform_py)
                    module = module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'fetch_data') and callable(module.fetch_data):
                        for query in queries:
                            print('Fetching data from', platform_py, 'for query:', query)
                            data = module.fetch_data(query)
                            os.makedirs(f'fetched/{module_name}/', exist_ok=True)
                            with open(f'fetched/{module_name}/{query}-{time.time()}.json', 'w') as f:
                                json.dump(data, f, indent=2)
                            print('File saved successfully!')
                except Exception as e:
                    print(f'Fetch from platform {platform} error: ', e)
    except Exception as e:
        print('Update db error:', e)
        raise e

    print('DB updated.')


if __name__ == '__main__':
    init()
    print('project-d service is running...')

    # Run the API
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    # Schedule the job to run every minute
    schedule.every().minute.do(update_db)
    print('DB update scheduled.')

    try:
        # Run the scheduler
        schedule.run_all()
        while True:
            schedule.run_pending()
            time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
    except KeyboardInterrupt:
        print('keyboard interrupt')
    finally:
        print('project-d service is stopping...')
        db.db_close()
        print('project-d service stopped.')
        exit(0)
