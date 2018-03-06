# -*- coding: utf-8 -*-

import json
import bcrypt
import pg8000

from os import environ
from collections import namedtuple


class Demo:
    """initialize the app with demo users and data
    this will also wipe out the database"""
    def __init__(self):
        self.usr = [("admin", "lifeuniverse"),
                    ("guest", "sixtimesnine")]
        # Time Magazine's Top 10 Novels
        self.lib = {"now": [{"title": "To Kill a Mockingbird",
                             "author": "Harper Lee"}],
                    "next": [{"title": "1984",
                              "author": "George Orwell"},
                             {"title": "The Lord of the Rings",
                              "author": "J.R.R. Tolkien"},
                             {"title": "The Catcher in the Rye",
                              "author": "J.D. Salinger"}],
                    "done": [{"title": "The Great Gatsby",
                              "author": "F. Scott Fitzgerald"},
                             {"title": "The Lion, the Witch, and the Wardrobe",
                              "author": "C.S. Lewis"},
                             {"title": "Lord of the Flies",
                              "author": "William Golding"},
                             {"title": "Animal Farm",
                              "author": "George Orwell"},
                             {"title": "Catch-22",
                              "author": "Joseph Heller"},
                             {"title": "The Grapes of Wrath",
                              "author": "John Steinbeck"}]}

    def start_fresh(self):
        """this wipes the database adds demo data"""
        self.db = DataBase()
        print("Initializing database...")
        self.db.init_db()

        print("Creating users...")
        for username, password in self.usr:
            self.db.add_user(username, password)

        print("Inserting books...")
        for status, books in self.lib.items():
            for b in books:
                request = {"book": b, "status": status}
                self.db.add_book("guest", request)
        print("Done.")


class DataBase:
    """several database utilities"""
    Conn = namedtuple("Conn", "user, password, host, port, database")

    def __init__(self):
        self.db_url = self._get_db_url()

    def _get_db_url(self):
        try:
            return environ["DATABASE_URL"]
        except KeyError:
            msg = """ERROR: Please set a DATABASE_URL environment variable such as:
        DATABASE_URL=postgres://user:pass@postgres.example.com/mydb"""
            exit(msg)

    def _db_params(self):
        """parse database connection string of format:
        postgres://user:pass@host/table"""

        url = self.db_url.split("//")[1]
        auth, conn = url.split("@")
        username, password = auth.split(":")
        socket, database = conn.split("/")
        host, port = socket.split(":")
        return self.Conn(username, password, host, int(port), database)

    def _connect(self):
        """connects to database and creates a cursor"""
        params = self._db_params()
        conn = pg8000.connect(user=params.user,
                              password=params.password,
                              host=params.host,
                              port=params.port,
                              database=params.database,
                              ssl=True)
        cursor = conn.cursor()
        return cursor, conn

    def _disconnect(self, cursor, conn):
        """closes the cursor and connection to database"""
        cursor.close()
        conn.close()

    def _create_tables(self):
        accounts = """create table if not exists accounts (
        user_id serial primary key,
        username text not null,
        password text not null);"""

        library = """create table if not exists library (
        book_id serial primary key,
        user_id serial references accounts (user_id),
        book jsonb not null,
        status text check (status in ('now', 'next', 'done')));"""

        cursor, conn = self._connect()
        cursor.execute(accounts)
        cursor.execute(library)
        conn.commit()
        self._disconnect(cursor, conn)

    def _drop_tables(self):
        sql = "drop table if exists library, accounts cascade;"
        cursor, conn = self._connect()
        cursor.execute(sql)
        conn.commit()
        self._disconnect(cursor, conn)

    def add_user(self, username, password):
        """add a user to the database using bcrypt to hash their password"""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        db_hash = hashed.decode("utf-8")  # decode byte-string before storing

        sql = "insert into accounts (username, password) values (%s, %s);"
        cursor, conn = self._connect()
        cursor.execute(sql, (username, db_hash))
        conn.commit()
        self._disconnect(cursor, conn)

    def init_db(self):
        self._drop_tables()
        self._create_tables()

    def test_db(self):
        cursor, conn = self._connect()
        cursor.execute("SELECT version();")
        result = cursor.fetchall()
        conn.commit()
        print(result)
        self._disconnect(cursor, conn)

    def _get_user(self, username):
        """retrieves an account's ID and password hash"""
        sql = "select user_id, password from accounts where username = %s;"
        cursor, conn = self._connect()
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        conn.commit()
        self._disconnect(cursor, conn)

        if result is None:
            raise Exception("User Does Not Exist")
        else:
            return result[0], result[1]

        return result

    def _check_hash(self, password, db_hash):
        """check the password against the bcrypt hash"""
        hashed = db_hash.encode("utf-8")  # encode back into byte-string
        check = bcrypt.hashpw(password.encode("utf-8"), hashed)
        return True if check == hashed else False

    def authenticate(self, username, password):
        """authenticates a user logging in with HTTP Basic Auth"""
        try:
            user_id, hashed = self._get_user(username)
        except Exception:
            return False

        if user_id > 0 and self._check_hash(password, hashed):
            return True
        else:
            return False

    def _unpack(self, request, fields):
        params = []
        for f in fields:
            try:
                params.append(request[f])
            except Exception:
                raise Exception("missing required field: {}".format(f))
        return params

    def _formatone(self, row):
        try:
            return {"book_id": row[0], "book": row[1], "status": row[2]}
        except TypeError:
            raise Exception("Book Not Found")

    def _formatall(self, rows):
        tmp = []
        for r in rows:
            tmp.append(self._formatone(r))
        return tmp

    def fetchall(self, username):
        user_id, _ = self._get_user(username)
        cursor, conn = self._connect()
        sql = "select book_id, book, status from library where (user_id = %s and status = %s);"

        books = []
        for status in ("now", "next", "done"):
            cursor.execute(sql, (user_id, status))
            rows = cursor.fetchall()
            books.append(self._formatall(rows))

        conn.commit()
        self._disconnect(cursor, conn)

        _now, _next, _done = books
        response = {"now": _now, "next": _next, "done": _done}
        return response

    def fetchone(self, username, book_id):
        user_id, _ = self._get_user(username)
        cursor, conn = self._connect()
        sql = "select book_id, book, status from library where (user_id = %s and book_id = %s);"

        cursor.execute(sql, (user_id, book_id))
        book = cursor.fetchone()
        conn.commit()
        self._disconnect(cursor, conn)
        response = self._formatone(book)
        return response

    def add_book(self, username, request):
        user_id, _ = self._get_user(username)
        book, status = self._unpack(request, ["book", "status"])
        sql = """insert into library (user_id, book, status) values
 ((select user_id from accounts where user_id = %s), %s, %s)
 returning book_id, book, status;"""

        cursor, conn = self._connect()
        cursor.execute(sql, (user_id, json.dumps(book), status))
        row = cursor.fetchone()
        conn.commit()
        self._disconnect(cursor, conn)
        response = self._formatone(row)
        return response

    def edit_book(self, username, book_id, request):
        user_id, _ = self._get_user(username)
        op, value = self._unpack(request, ["op", "value"])
        new = json.dumps(value) if op == "book" else value
        sql = """update library set {} = %s where (user_id = %s and book_id = %s)
 returning book_id, book, status;""".format(op)

        cursor, conn = self._connect()
        cursor.execute(sql, (new, user_id, (book_id)))
        row = cursor.fetchone()
        conn.commit()
        self._disconnect(cursor, conn)
        response = self._formatone(row)
        return response

    def delete_book(self, username, book_id):
        user_id, _ = self._get_user(username)
        cursor, conn = self._connect()
        sql = """delete from library where (user_id = %s and book_id = %s)
 returning book_id, book, status;"""

        cursor.execute(sql, (user_id, book_id))
        row = cursor.fetchone()
        conn.commit()
        self._disconnect(cursor, conn)
        response = self._formatone(row)
        return response
