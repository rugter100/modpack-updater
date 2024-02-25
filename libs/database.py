import sqlite3


class _cache(object):

    def __init__(self):
        self.data = {}

    def __setitem__(self, keys, item):
        self.data[keys] = [item]

    def __getitem__(self, keys):
        value = self.data[keys][0]
        return value

    def getcount(self, keys):
        return self.data[keys][0]

    def listkeys(self):
        return list(self.data)

class sqlite():

    def __init__(self):
        self.db = _cache()
        self.connected_database = "Null"

    def connect(self, database):
        try:
            self.db['db', database] = sqlite3.connect(database)
            self.db['cursor', database] = self.db['db', database].cursor()
            self.connected_database = database
            self.db['db', database].commit()
        except mysql.connector.errors.DatabaseError as err:
            raise Exception(err)

    def disconnect(self, database=False, comm=True):
        if not database:
            database = self.connected_database
        if comm:
            self.db['db', database].commit()
        self.db['db', database].close()

    def commit(self, database=False):
        if not database:
            database = self.connected_database
        self.db['db', database].commit()

    def custom_query(self, query, values=False, database=False, comm=True):
        if not database:
            database = self.connected_database
        if not values:
            output = self.db['cursor', database].execute(query)
        else:
            output = self.db['cursor', database].execute(query, values)
        if comm:
            self.db['db', database].commit()
        return output.fetchall()

    def create_table(self, table, values, database=False, comm=True):
        if not database:
            database = self.connected_database
        self.db['cursor', database].execute(f"CREATE TABLE IF NOT EXISTS {table} ({values})")
        if comm:
            self.db['db', database].commit()

    #def create_collumn(self, database, table, collumn, type):
    #    self.db['cursor' ,database].execute(f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME={table} AND COLUMN_NAME={collumn}) BEGIN ALTER TABLE {table} ADD '{collumn}' '{type}' NULL END")

    def drop_table(self, table, database=False, comm=True):
        if not database:
            database = self.connected_database
        self.db['cursor', database].execute(f'DROP TABLE IF EXISTS {table}')
        if comm:
            self.db['db', database].commit()

    def insert(self, table, collumns, values, database=False, comm=True):
        if not database:
            database = self.connected_database
        self.db['cursor', database].execute(f"INSERT INTO {table} ({collumns}) VALUES ({values})")
        if comm:
            self.db['db', database].commit()

    def insertmultiple(self, table, collumns=str, values=list, database=False, comm=True):
        if not database:
            database = self.connected_database
        for value in values:
            self.insert(table=table, collumns=collumns, values=value, database=database, comm=False)
        if comm:
            self.db['db', database].commit()

    def insert_if_not_exists(self, table, collumns, values, database=False, comm=True, filters=""):
        exists = self.rowcount(table=table, filters=filters, database=database, comm=comm)
        if not exists:
            self.insert(table, collumns, values, database, comm)
        return exists

    def update(self, table, collumn, value, filters="", database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        self.db['cursor', database].execute(f"UPDATE {table} SET {collumn} = '{value}'{filters}")
        if comm:
            self.db['db', database].commit()

    def updatemultiple(self, table, updates, filters="", values=False, database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        if values:
            self.db['cursor', database].execute(f"UPDATE {table} SET {updates}{filters}", values)
        else:
            self.db['cursor', database].execute(f"UPDATE {table} SET {updates}{filters}")
        if comm:
            self.db['db', database].commit()

    def delete(self, table, filters="", database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        self.db['cursor', database].execute(f"DELETE FROM {table}{filters}")
        if comm:
            self.db['db', database].commit()

    def fetchone(self, table, values='*', filters="", database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        self.db['cursor', database].execute(f"SELECT {values} FROM {table}{filters}")
        if comm:
            self.db['db', database].commit()
        return self.db['cursor', database].fetchone()

    def fetchall(self, table, values='*', filters="", order_by="", database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        if order_by != "":
            order_by = f" ORDER BY {order_by}"
        self.db['cursor', database].execute(f"SELECT {values} FROM {table}{filters}{order_by}")
        if comm:
            self.db['db', database].commit()
        return self.db['cursor', database].fetchall()

    def rowcount(self, table, values="*", filters="", database=False, comm=True):
        if not database:
            database = self.connected_database
        if filters != "":
            filters = f" WHERE {filters}"
        self.db['cursor', database].execute(f"SELECT {values} FROM {table}{filters}")
        if comm:
            self.db['db', database].commit()
        return self.db['cursor', database].rowcount

    def dict_getone(self, table, key):
        data = self.fetchone(table=table, filters=f'itemkey="{key}"')
        return [data[0], data[1], data[2]]

    def dict_getall(self, table):
        data = self.fetchall(table)
        dictionary = {}
        for item in data:
            dictionary[item[1]] = [item[2], item[0]]
        return dictionary