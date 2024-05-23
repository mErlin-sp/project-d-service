import os
import time
from threading import Thread

import schedule
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import worker
from db import DB

# DB connection parameters
db_host: str = os.getenv('MYSQL_ADDR', '127.0.0.1')
db_port: int = int(os.getenv('MYSQL_PORT', 3306))
db_user: str = os.getenv('MYSQL_USER', 'root')
db_password: str = os.getenv('MYSQL_PASSWORD', 'qwertyuiop')
db_database: str = os.getenv('MYSQL_DB', 'project-d-db')

# Initialize DB
db = DB(db_host, db_port, db_user, db_password, db_database)

# API parameters
api_host: str = os.getenv('API_ADDR', '127.0.0.1')
api_port: int = int(os.getenv('API_PORT', 8000))

# Initialize FastAPI
api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

platforms_dir = 'platforms/'


@api.get("/")
async def root():
    return {"message": "Service is running..."}


@api.get("/test/{message}")
async def test_api(message: str):
    return {"message": message}


@api.get("/db/queries")
async def get_queries():
    return db.get_queries()


@api.get("/db/queries/active")
async def get_active_queries():
    return {"rows": db.get_active_queries()}


@api.get("/db/query/{query_id}/active/{active}")
async def set_query_status(query_id: int, active: bool):
    db.set_query_status(query_id, active)
    return {'status': 'ok', 'query_id': query_id, 'active': active}


@api.get("/db/queries/add-query/{query}")
async def add_query(query: str):
    return {'status': 'ok', 'query': query, 'query_id': db.add_query(query)}


@api.get("/platforms")
async def get_platforms():
    return [platform[0] for platform in worker.list_platforms(platforms_dir)]


@api.get("/db/goods")
async def get_goods():
    return db.get_goods()


@api.get("/db/prices/{good_id}")
async def get_prices(good_id: int):
    return db.get_prices(good_id)


@api.get("/db/in-stock/{good_id}")
async def get_in_stock(good_id: int):
    return db.get_in_stock(good_id)


def run_api():
    print('Running API...')
    print('API Host:', api_host)
    print('API Port:', api_port)
    print('')
    uvicorn.run(api, host=api_host, port=api_port)
    print('API is running...')


def init():
    print('project-d service is initializing...')
    db.db_init()
    print('project-d service is initialized.')


if __name__ == '__main__':
    init()
    print('project-d service is running...')

    # Run the API
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    # Schedule the job to run every minute
    schedule.every(5).minutes.do(worker.update_db, db, platforms_dir)
    print('DB update scheduled.')
    print('--' * 50)
    print('')

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
