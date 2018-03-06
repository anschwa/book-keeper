# -*- coding: utf-8 -*-

import bottle
from sys import argv
from utils import DataBase, Demo

HOST = "0.0.0.0"
PORT = argv[1]
DB = DataBase()
DEMO = Demo()


# --- WebApp --- #
@bottle.route("/", method="GET")
@bottle.auth_basic(DB.authenticate)
def index():
    user, _ = bottle.request.auth
    return bottle.template("index.html", user=user)


@bottle.route("/static/<path:path>")
def css(path):
    if path in ("style.css", "client.js", "favicon.ico"):
        return bottle.static_file(path, "./static/")


# --- API --- #
def execute(func, *args, status=200):
    try:
        response = func(*args)
    except Exception as err:
        bottle.response.status = 400
        return {"error": repr(err)}
    else:
        bottle.response.status = status
        return response


@bottle.route("/reset", method="GET")
@bottle.auth_basic(DB.authenticate)
def reset():
    user, _ = bottle.request.auth
    if user == "admin":
        execute(DEMO.start_fresh)
        return {"success": "Database initialized."}
    else:
        bottle.response.status = 403
        return {"error": "Permission Denied."}


@bottle.route("/book", method="GET")
@bottle.auth_basic(DB.authenticate)
def fetch_books():
    user, _ = bottle.request.auth
    return execute(DB.fetchall, user)


@bottle.route("/book", method="POST")
@bottle.auth_basic(DB.authenticate)
def add_book():
    user, _ = bottle.request.auth
    req = bottle.request.json
    return execute(DB.add_book, user, req, status=201)


@bottle.route("/book/<book_id:int>", method="GET")
@bottle.auth_basic(DB.authenticate)
def get_book(book_id):
    user, _ = bottle.request.auth
    return execute(DB.fetchone, user, book_id)


@bottle.route("/book/<book_id:int>", method="PATCH")
@bottle.auth_basic(DB.authenticate)
def edit_book(book_id):
    user, _ = bottle.request.auth
    req = bottle.request.json

    response = []
    for patch in req:
        tmp = execute(DB.edit_book, user, book_id, patch)
        response.append(tmp)

    return {"updated": response}


@bottle.route("/book/<book_id:int>", method="DELETE")
@bottle.auth_basic(DB.authenticate)
def delete_book(book_id):
    user, _ = bottle.request.auth
    return execute(DB.delete_book, user, book_id, status=204)


if __name__ == "__main__":
    # Launch webapp
    bottle.run(host=HOST, port=PORT)
