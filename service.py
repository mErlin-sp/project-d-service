import logging
import os
import sys
import time
from threading import Thread

import schedule
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

import config
import exporter
import worker
from db import SqLiteDB, MySQLDB

start_time = time.time()

debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
config_file: str = os.getenv('CONFIG_FILE', 'config.ini')

db_type: str = os.getenv('DB_TYPE', 'sqlite')

if db_type == 'sqlite':
    db_dir: str = os.getenv('DB_DIR', 'db/')
    db_name: str = os.getenv('DB_NAME', 'project-d-db.sqlite')
    db = SqLiteDB(db_name, db_dir)
elif db_type == 'mysql':
    # DB connection parameters
    db_host: str = os.getenv('MYSQL_ADDR', '127.0.0.1')
    db_port: int = int(os.getenv('MYSQL_PORT', 3306))
    db_user: str = os.getenv('MYSQL_USER', 'root')
    db_password: str = os.getenv('MYSQL_PASSWORD', 'qwertyuiop')
    db_database: str = os.getenv('MYSQL_DB', 'project-d-db')

    # Initialize DB
    db = MySQLDB(db_host, db_port, db_user, db_password, db_database)
else:
    print('Invalid DB_TYPE:', db_type)
    exit(0)

# API parameters
api_host: str = os.getenv('API_ADDR', '127.0.0.1')
api_port: int = int(os.getenv('API_PORT', 8000))

# Initialize FastAPI
api = FastAPI()

if debug:
    print('Adding CORS middleware...')
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


if debug:
    @api.get("/test/{message}")
    async def test_api(message: str):
        return {"message": message}


@api.get("/db/type")
async def get_db_type():
    return {'db_type': db_type}


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


@api.get("/settings/update-interval")
async def get_update_interval():
    return {'update_interval': config.read_config_value('UpdateInterval')}


@api.get("/settings/update-interval/{interval}")
async def set_update_interval(interval: int):
    config.write_config_value('UpdateInterval', str(interval))
    return {'update_interval': config.read_config_value('UpdateInterval')}


@api.get("/export/csv")
async def export_to_csv():
    file_name = f'export-{time.strftime("%Y-%m-%d %H-%M-%S")}.csv'
    exported = exporter.export_to_csv(db, file_name=file_name, file_path='export/')
    if exported:
        return FileResponse(exported, media_type='text/csv', filename=file_name)
    else:
        return {'status': 'error', 'message': 'Export to CSV failed'}


@api.get("/export/xlsx")
async def export_to_xlsx():
    file_name = f'export-{time.strftime("%Y-%m-%d %H-%M-%S")}.xlsx'
    exported = exporter.export_to_xlsx(db, file_name=file_name, file_path='export/')
    if exported:
        return FileResponse(exported, media_type='application/vnd.ms-excel',
                            filename=file_name)
    else:
        return {'status': 'error', 'message': 'Export to XLSX failed'}


@api.get("/export/sqlite-db")
async def export_sqlite_db():
    if db_type == 'sqlite':
        db_file = os.path.join(db_dir, db_name)
        if not os.path.exists(db_file):
            return {'status': 'error', 'message': 'DB file not found'}
        return FileResponse(db_file, media_type='application/x-sqlite3', filename=db_name)
    else:
        return {'status': 'error', 'message': 'DB_TYPE is not sqlite'}


@api.get("/restart-service")
async def restart_service():
    try:
        print('Restarting service...')
        os._exit(0)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@api.get("/settings/db-type")
async def get_db_type():
    return {'db_type': db_type}


@api.get("/statistics")
async def get_statistics():
    return {'running_time': round(time.time() - start_time, 2),
            'update_interval': config.read_config_value('UpdateInterval')}


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

    # # Export the DB to CSV and XLSX. Test
    # exporter.export_to_csv(db, file_name='export.csv', file_path='export/')
    # exporter.export_to_xlsx(db, file_name='export.xlsx', file_path='export/')
    # exit(0)


if __name__ == '__main__':
    logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.INFO)

    init()
    print('project-d service is running...')

    # Run the API
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    # Schedule the job to run every minute
    schedule.every(int(config.read_config_value('UpdateInterval'))).minutes.do(worker.update_db, db, platforms_dir)
    print('DB update scheduled. Interval:', config.read_config_value('UpdateInterval'), 'minutes')
    print('--' * 50)
    print('')

    try:
        # if debug:
        #     print('Running the scheduler...')
        #     # Run the scheduler
        #     schedule.run_all()
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
