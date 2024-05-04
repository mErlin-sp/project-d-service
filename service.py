import time
from threading import Thread

import schedule
import uvicorn
from fastapi import FastAPI

import worker
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


if __name__ == '__main__':
    init()
    print('project-d service is running...')

    # Run the API
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    # Schedule the job to run every minute
    schedule.every().minute.do(worker.update_db, db, platforms_dir)
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
