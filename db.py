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
                    ID INT NOT NULL AUTO_INCREMENT,
                    NAME VARCHAR(255) NOT NULL,
                    PRIMARY KEY (ID)
                );
            ''')
            print('tracked_queries table created')

            # Update tracked_queries table
            cur.execute('''
                INSERT INTO tracked_queries (ID, NAME) VALUES (1, 'Iphone 12 64GB Blue')
                ON DUPLICATE KEY UPDATE NAME = 'Iphone 12 64GB Blue';
            ''', {'raise_on_warnings': True})

            # Make sure data is committed to the database
            self.cnx.commit()
            print('tracked_queries table updated')

        except mysql.connector.Error as e:
            print('DB Init Error:', e)
            exit(0)
        else:
            print('DB Init successful')
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
            print('Get Requests Error:', e)
            return []

    def db_close(self):
        try:
            self.cnx.close()
            print('DB Connection closed')
        except mysql.connector.Error as e:
            print('DB Close Error:', e)
