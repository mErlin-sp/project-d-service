import os
import sqlite3
import threading
from typing import Sequence

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection


class DB:
    def __init__(self, cnx: PooledMySQLConnection | MySQLConnectionAbstract | sqlite3.Connection, database: str,
                 db_type: str):
        self.cnx: PooledMySQLConnection | MySQLConnectionAbstract | sqlite3.Connection = cnx
        self.database: str = database
        self.db_type: str = db_type

        # Create a lock
        self.lock = threading.Lock()
        self.initialized = False

    def db_init(self):
        if self.initialized:
            return

        print('DB Init...')
        try:
            # Get a cursor
            cur = self.cnx.cursor()
            print('Cursor created')

            if self.db_type == 'mysql':
                # Execute a query
                cur.execute("SELECT CURDATE()")

                # Fetch one result
                row = cur.fetchone()
                print("Current date is: {0}".format(row[0]))

            # Create a tracked_queries table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tracked_queries (
                    id {} NOT NULL PRIMARY KEY {},
                    query VARCHAR(255) NOT NULL,
                    active BOOLEAN DEFAULT TRUE
                );
            '''.format('INTEGER' if self.db_type == 'sqlite' else 'INT',
                       'AUTOINCREMENT' if self.db_type == 'sqlite' else 'AUTO_INCREMENT'))
            print('tracked_queries table created')

            # Update tracked_queries table
            if self.db_type == 'sqlite':
                cur.execute('''
                    REPLACE INTO tracked_queries (id, query) VALUES (1, 'Iphone 12 64GB');
                ''')
            elif self.db_type == 'mysql':
                cur.execute('''
                    INSERT INTO tracked_queries (id, query) VALUES (1, 'Iphone 12 64GB')
                    ON DUPLICATE KEY UPDATE query = 'Iphone 12 64GB';
                ''')

            print('tracked_queries table updated')

            # Create goods table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS goods (
                    id {int} PRIMARY KEY {auto_increment},
                    platform VARCHAR(255) NOT NULL,
                    platform_id BIGINT UNSIGNED NOT NULL,
                    query_id INT NOT NULL,
                    name VARCHAR(512) NOT NULL,
                    href VARCHAR(2048) NOT NULL,
                    img_href VARCHAR(2048),
                    brand VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP {on_update},
                    last_confirmed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES tracked_queries(id)
                );
            '''.format(int='INTEGER' if self.db_type == 'sqlite' else 'INT',
                       auto_increment='AUTOINCREMENT' if self.db_type == 'sqlite' else 'AUTO_INCREMENT',
                       on_update='ON UPDATE CURRENT_TIMESTAMP' if self.db_type == 'mysql' else ''))

            print('goods table created')

            if self.db_type == 'sqlite':
                # Creating a trigger to update `last_updated` on row update
                cur.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_goods_last_updated
                    AFTER UPDATE ON goods
                    FOR EACH ROW
                    BEGIN
                        UPDATE goods SET last_updated = CURRENT_TIMESTAMP WHERE id = OLD.id;
                    END;
                ''')
                print('Trigger update_goods_last_updated created')

            # Create prices table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id {int} PRIMARY KEY {auto_increment},
                    good_id INT NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (good_id) REFERENCES goods(id)
                );
            '''.format(int='INTEGER' if self.db_type == 'sqlite' else 'INT',
                       auto_increment='AUTOINCREMENT' if self.db_type == 'sqlite' else 'AUTO_INCREMENT'))
            print('prices table created')

            # Create in_stock table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS in_stock (
                    id {int} PRIMARY KEY {auto_increment},
                    good_id INT NOT NULL,
                    in_stock BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (good_id) REFERENCES goods(id)
                );
            '''.format(int='INTEGER' if self.db_type == 'sqlite' else 'INT',
                       auto_increment='AUTOINCREMENT' if self.db_type == 'sqlite' else 'AUTO_INCREMENT'))

            # Make sure data is committed to the database
            self.cnx.commit()

        except mysql.connector.Error if self.db_type == 'mysql' else sqlite3.Error as e:
            print('DB Init Error:', e)
            exit(0)
        else:
            print('DB Init successful')
            print('--' * 50)
            print('')
            cur.close()
            self.initialized = True

    def db_close(self):
        if not self.initialized:
            return

        try:
            self.cnx.close()
            print('DB Connection closed')
        except mysql.connector.Error as e:
            print('DB Close Error:', e)

    def get_queries(self):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                cur.execute('SELECT * FROM tracked_queries')

                # Fetch all results
                rows = cur.fetchall()
                cur.close()
                return rows

            except mysql.connector.Error as e:
                print('Get Queries Error:', e)
                return []

    def get_active_queries(self):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                cur.execute('SELECT id,query FROM tracked_queries WHERE active = TRUE')

                # Fetch all results
                rows = cur.fetchall()
                cur.close()

                return rows
            except mysql.connector.Error as e:
                print('Get Queries Error:', e)
                return []

    def set_query_status(self, query_id: int, active: bool):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('UPDATE tracked_queries SET active = %s WHERE id = %s', (active, query_id))
                elif self.db_type == 'sqlite':
                    cur.execute('UPDATE tracked_queries SET active = ? WHERE id = ?', (active, query_id))

                # Make sure data is committed to the database
                self.cnx.commit()

                cur.close()
            except mysql.connector.Error as e:
                print('Set Query Status Error:', e)

    def add_query(self, query: str):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('INSERT INTO tracked_queries (query) VALUES (%s)', (query,))
                elif self.db_type == 'sqlite':
                    cur.execute('INSERT INTO tracked_queries (query) VALUES (?)', (query,))

                # Make sure data is committed to the database
                self.cnx.commit()

                return cur.lastrowid
            except mysql.connector.Error as e:
                print('Add Query Error:', e)
                return -1
            finally:
                cur.close()

    def execute_query(self, query: str, last_row_id=False, params: Sequence = ()):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                cur.execute(query, params)

                if last_row_id:
                    return cur.lastrowid

                return cur.fetchall()

            except mysql.connector.Error as e:
                print('Execute Query Error:', e)
                raise e
            finally:
                # Make sure data is committed to the database
                self.cnx.commit()

    def get_goods(self):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                cur.execute('SELECT * FROM goods')

                # Fetch all results
                rows = cur.fetchall()
                cur.close()
                return rows

            except mysql.connector.Error as e:
                print('Get Goods Error:', e)
                return []

    def get_prices(self, good_id: int):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('SELECT price,timestamp FROM prices WHERE good_id = %s', (good_id,))
                elif self.db_type == 'sqlite':
                    cur.execute('SELECT price,timestamp FROM prices WHERE good_id = ?', (good_id,))

                # Fetch all results
                rows = cur.fetchall()
                cur.close()
                return rows

            except mysql.connector.Error as e:
                print('Get Prices Error:', e)
                return []

    def get_in_stock(self, good_id: int):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('SELECT in_stock,timestamp FROM in_stock WHERE good_id = %s', (good_id,))
                elif self.db_type == 'sqlite':
                    cur.execute('SELECT in_stock,timestamp FROM in_stock WHERE good_id = ?', (good_id,))

                # Fetch all results
                rows = cur.fetchall()
                cur.close()
                return rows

            except mysql.connector.Error as e:
                print('Get In Stock Error:', e)
                return []

    def get_good_id(self, platform_id: int, query_id: int):
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('SELECT id FROM goods WHERE platform_id = %d AND query_id = %s',
                                (platform_id, query_id))
                elif self.db_type == 'sqlite':
                    cur.execute('SELECT id FROM goods WHERE platform_id = ? AND query_id = ?', (platform_id, query_id))

                # Fetch all results
                rows = cur.fetchall()
                cur.close()
                return rows

            except mysql.connector.Error as e:
                print('Get Good ID Error:', e)
                return []

    def add_good(self, platform: str, platform_id: int, query_id: int, name: str, href: str, img_href: str,
                 brand: str) -> int:
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('''
                        INSERT INTO goods (platform,platform_id, query_id, name, href, img_href, brand) VALUES (
                        %s, %s, %s, %s, %s, %s, %s)
                    ''', (platform, platform_id, query_id, name, href, img_href, brand))
                elif self.db_type == 'sqlite':
                    cur.execute('''
                        INSERT INTO goods (platform,platform_id, query_id, name, href, img_href, brand) VALUES (
                        ?, ?, ?, ?, ?, ?, ?)
                    ''', (platform, platform_id, query_id, name, href, img_href, brand))

                # Make sure data is committed to the database
                self.cnx.commit()

                return cur.lastrowid
            except mysql.connector.Error as e:
                print('Insert Good Error:', e)
                return -1
            finally:
                cur.close()

    def add_price(self, good_id: int, price: float) -> int:
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('INSERT INTO prices (good_id, price) VALUES (%s, %s)', (good_id, price))
                elif self.db_type == 'sqlite':
                    cur.execute('INSERT INTO prices (good_id, price) VALUES (?, ?)', (good_id, price))

                # Make sure data is committed to the database
                self.cnx.commit()

                return cur.lastrowid
            except mysql.connector.Error as e:
                print('Insert Price Error:', e)
                return -1
            finally:
                cur.close()

    def add_in_stock(self, good_id: int, in_stock: bool) -> int:
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('INSERT INTO in_stock (good_id, in_stock) VALUES (%s, %s)', (good_id, in_stock))
                elif self.db_type == 'sqlite':
                    cur.execute('INSERT INTO in_stock (good_id, in_stock) VALUES (?, ?)', (good_id, in_stock))

                # Make sure data is committed to the database
                self.cnx.commit()

                return cur.lastrowid
            except mysql.connector.Error as e:
                print('Insert In Stock Error:', e)
                return -1
            finally:
                cur.close()

    def update_last_confirmed(self, good_id: int, last_confirmed: str) -> int:
        with self.lock:
            try:
                # Get a cursor
                cur = self.cnx.cursor()

                # Execute a query
                if self.db_type == 'mysql':
                    cur.execute('UPDATE goods SET last_confirmed = %s WHERE id = %s', (last_confirmed, good_id))
                elif self.db_type == 'sqlite':
                    cur.execute('UPDATE goods SET last_confirmed = ? WHERE id = ?', (last_confirmed, good_id))

                # Make sure data is committed to the database
                self.cnx.commit()

                return cur.lastrowid
            except mysql.connector.Error as e:
                print('Update Last Confirmed Error:', e)
                return -1
            finally:
                cur.close()


class MySQLDB(DB):
    def __init__(self, host: str, port: int, user: str, password: str, database: str = 'project-d-db'):

        self.host = host
        self.port = port
        self.user = user
        self.password = password

        print('MySQL DB')
        print('DB Connection parameters:')
        print('Host:', self.host)
        print('Port:', self.port)
        print('User:', self.user)
        print('')

        try:
            # Connect to server
            cnx = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database)

            if not cnx.is_connected():
                raise mysql.connector.Error('Failed to connect to MySQL server.')

            print('Connected to MySQL server.')

            super().__init__(cnx, database, 'mysql')

        except mysql.connector.Error as e:
            print('DB Init Error:', e)
            exit(0)


class SqLiteDB(DB):
    def __init__(self, db_name: str = 'project-d-db.sqlite', db_dir: str = 'db/'):

        print('SQLite DB')
        print('DB Connection parameters:')
        print('DB:', db_name)
        print('DB Dir:', db_dir)
        print('')

        try:
            # Connect to server
            os.makedirs(db_dir, exist_ok=True)
            cnx = sqlite3.connect(os.path.join(db_dir, db_name), check_same_thread=False)

            print('Connected to SQLite server.')

            super().__init__(cnx, db_name, 'sqlite')

        except sqlite3.Error as e:
            print('DB Init Error:', e)
            exit(0)
