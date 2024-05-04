import mysql.connector


class DB:
    def __init__(self, host: str = '127.0.0.1', port: int = 3306, user: str = 'root', password: str = 'qwertyuiop',
                 database: str = 'project-d-db'):
        self.cnx = None
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def __del__(self):
        if self.cnx is not None:
            self.db_close()

    def db_init(self):
        print('DB Init...')
        try:
            # Connect to server
            self.cnx = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database)

            if not self.cnx.is_connected():
                raise mysql.connector.Error('Failed to connect to MySQL server.')

            print('Connected to MySQL server.')

            # Get a cursor
            cur = self.cnx.cursor()
            print('Cursor created')

            # Execute a query
            cur.execute("SELECT CURDATE()")

            # Fetch one result
            row = cur.fetchone()
            print("Current date is: {0}".format(row[0]))

            # Create a tracked_queries table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tracked_queries (
                    id INT NOT NULL AUTO_INCREMENT,
                    query VARCHAR(255) NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (ID)
                );
            ''')
            print('tracked_queries table created')

            # Update tracked_queries table
            cur.execute('''
                INSERT INTO tracked_queries (id, query) VALUES (1, 'Iphone 12 64GB')
                ON DUPLICATE KEY UPDATE query = 'Iphone 12 64GB';
            ''')
            print('tracked_queries table updated')

            # Create goods table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS goods (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    platform VARCHAR(255) NOT NULL,
                    platform_id INT NOT NULL,
                    query_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    href VARCHAR(255) NOT NULL,
                    img_href VARCHAR(255),
                    brand VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES tracked_queries(id)
                );
            ''')
            print('goods table created')

            # Create prices table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    good_id INT NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (good_id) REFERENCES goods(id)
                );
            ''')
            print('prices table created')

            # Make sure data is committed to the database
            self.cnx.commit()

        except mysql.connector.Error as e:
            print('DB Init Error:', e)
            exit(0)
        else:
            print('DB Init successful')
            print('--' * 50)
            print('')
            cur.close()

    def get_queries(self):
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

    def execute_query(self, query: str, _kwargs=None, last_row_id=False):
        if _kwargs is None:
            _kwargs = []
        try:
            # Get a cursor
            cur = self.cnx.cursor()

            # Execute a query
            cur.execute(query, _kwargs)

            if last_row_id:
                return cur.lastrowid

            return cur.fetchall()

        except mysql.connector.Error as e:
            print('Execute Query Error:', e)
            raise e
        finally:
            # Make sure data is committed to the database
            self.cnx.commit()

    def db_close(self):
        try:
            self.cnx.close()
            print('DB Connection closed')
        except mysql.connector.Error as e:
            print('DB Close Error:', e)
