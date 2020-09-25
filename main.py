from flask import Flask, request, escape, jsonify, g
from werkzeug.exceptions import HTTPException
from traceback import format_exc
from os import urandom
from random import shuffle
from validators import Validator, ValidateError
import sqlite3
import json

app = Flask(__name__)

DATABASE = 'db/clients.sqlite'

validators = {}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def verify_user(uid: str, token: str):
    if not uid or not token:
        return False
    try:
        app.logger.warn(f"Query uid {uid} token {token}")
        res = query_db('SELECT * FROM AUTHDATA WHERE uid=? AND token=?', [uid, token])
        app.logger.warn("!! {}".format(res))
        if len(res) == 0:
            return False
    except Exception as e:
        app.logger.error("Error during adding entry to AUTHDATA table: {}".format(format_exc(e)))
        return False
    return True


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.before_first_request
def startup():
    validators['uid'] = Validator("UID/TOKEN validator", r"^[0-9a-f]{32}$")
    validators['token'] = validators['uid']
    validators['slot'] = Validator("PORT/SLOT validator", r"^[0-9]+$")
    validators['port'] = validators['slot']
    validators['config'] = Validator("CONFIG validator", r"^[a-zA-Z0-9\=\/\\]*$")

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": 2,
        "msg": {
            "code": e.code,
            "name": e.name,
            "description": e.description
        }
    })
    response.content_type = "application/json"
    return response


@app.errorhandler(ValidateError)
def handle_malformed_data(e):
    response = {
        "code": 2,
        "msg": "Malformed data in parameter: {}".format(e)
    }
    return response


@app.route('/get', methods=['POST'])
def get():
    ip = request.remote_addr
    resp = {"code": 3, "msg": "Unimplemented", "config": ""}

    uid = request.form.get('uid')
    token = request.form.get('token')
    validators['uid'].validate(uid)
    validators['token'].validate(token)

    if not verify_user(uid, token):
        app.logger.warn("Unauthorized request from {}".format(ip))
        resp["code"] = 1
        resp["msg"] = "Unauthorized"
        return resp
    # OK

    # get some config from db
    try:
        res = query_db("SELECT uid,ip,port,slot_info FROM CLIENTS WHERE NOT uid=?", [uid])
        if len(res) == 0:
            app.logger.error("No entry in CLIENTS for uid: {}".format(uid))
            resp["code"] = 3
            resp["msg"] = "Internal error"
            return resp
        # json is like {"used": [], "unused": [0, 1, 2]}
        shuffle(res)
        srv = None
        for o in res:
            o = list(o)
            obj = json.loads(o[3])
            if len(obj["unused"]) != 0:
                e = obj['unused'][0]
                app.logger.warn("Selected server: {}; slot: {}".format(o, e))
                del obj['unused'][0]
                obj['used'].append(e)
                obj['used'].sort()
                obj['unused'].sort()
                o[3] = json.dumps(obj)
                srv = o
                app.logger.warn("New srv entry: {}".format(srv))
                break

        if not srv:
            resp["code"] = 3
            resp["msg"] = "Internal error: can't choose server"
            return resp

        query_db("UPDATE CLIENTS SET slot_info=? WHERE uid=?", [srv[3], srv[0]])

        # todo read file here
        config = "unimplemented"
        #

        resp["code"] = 0
        resp["msg"] = "OK"
        resp["config"] = config
    except Exception as e:
        app.logger.error("Error during adding entry to CLIENTS table: {}".format(format_exc(e)))
        resp["code"] = 3
        resp["msg"] = "Internal error"
        return resp

    get_db().commit()
    return resp


@app.route('/push', methods=['POST'])
def push():
    ip = request.remote_addr
    resp = {"code": 0, "msg": "OK"}

    # check auth data
    uid = request.form.get('uid')
    token = request.form.get('token')
    validators['uid'].validate(uid)
    validators['token'].validate(token)

    if not verify_user(uid, token):
        app.logger.warn("Unauthorized request from {}".format(ip))
        resp["code"] = 1
        resp["msg"] = "Unauthorized"
        return resp
    # OK

    port = request.form.get('port', type=int)

    if not port or port < 1 or port > 65535:
        resp['code'] = 2
        resp['msg'] = "Malformed data: port value is invalid or null"
        return resp

    try:
        res = query_db('UPDATE CLIENTS SET port=?, ip=? WHERE uid=?', [port, ip, uid])
    except Exception as e:
        app.logger.error("Error during adding entry to CLIENTS table: {}".format(format_exc(e)))
        resp["code"] = 3
        resp["msg"] = "Internal error"
        return resp
    get_db().commit()
    return resp


@app.route('/update', methods=['POST'])
def update():
    ip = request.remote_addr
    resp = {"code": 3, "msg": "Unimplemented"}

    uid = request.form.get('uid')
    token = request.form.get('token')
    config = request.form.get('config')
    validators['uid'].validate(uid)
    validators['token'].validate(token)
    validators['config'].validate(config)

    if not verify_user(uid, token):
        app.logger.warn("Unauthorized request from {}".format(ip))
        resp["code"] = 1
        resp["msg"] = "Unauthorized"
        return resp
    


    return resp


@app.route('/register', methods=['POST'])
def register():
    ip = request.remote_addr
    resp = {"code": 3, "msg": "Internal error", "uid": "", "token": ""}

    uid, token = urandom(16).hex(), urandom(16).hex()

    try:
        res = query_db('INSERT INTO AUTHDATA (uid,token) VALUES (?,?)', [uid, token])
    except Exception as e:
        app.logger.error("Error during adding entry to AUTHDATA table: {}".format(format_exc(e)))
        resp["code"] = 3
        resp["msg"] = "Internal error"
        return resp
    app.logger.warn("Insertion result: {}".format(res))

    try:
        res = query_db('INSERT INTO CLIENTS (uid,ip,port,country,slot_info) VALUES (?,?,?,?,?)',
                       [uid, ip, -1, 'UNKNOWN', json.dumps({"used": [], "unused": [i for i in range(3)]})])
    except Exception as e:
        app.logger.error("Error during adding entry to CLIENTS table: {}".format(format_exc(e)))
        resp["code"] = 3
        resp["msg"] = "Internal error"
        return resp

    app.logger.warn("Insertion result: {}".format(res))
    resp["code"] = 0
    resp["msg"] = "OK"
    resp["uid"] = uid
    resp["token"] = token
    get_db().commit()
    return resp


@app.route('/', methods=['GET', 'POST'])
def default_route():
    resp = {"code": 0, "msg": "OK"}
    return resp
