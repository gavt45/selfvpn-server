from flask import Flask, request,escape,jsonify,g
from werkzeug.exceptions import HTTPException
from traceback import format_exc
from os import urandom
import sqlite3
import json

app = Flask(__name__)

DATABASE = 'db/clients.sqlite'

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

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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

@app.route('/get', methods=['POST'])
def get():
    resp = {"code": 3, "msg": "Unimplemented"}
    return resp

@app.route('/push', methods=['POST'])
def push():
    ip = request.remote_addr
    resp = {"code": 0, "msg": "OK"}

    # check auth data
    uid = request.form.get('uid')
    token = request.form.get('token')

    if not uid or not token:
        resp['code'] = 1
        resp['msg'] = "Unauthorized"
        return resp
    try:
        res = query_db('SELECT * FROM AUTHDATA WHERE uid=? AND token=?', [uid, token])
        if len(res) == 0:
            resp['code'] = 1
            resp['msg'] = "Unauthorized"
            return resp
    except Exception as e:
        app.logger.error("Error during adding entry to AUTHDATA table: {}".format(format_exc(e)))
        resp["code"] = 3
        resp["msg"] = "Internal error"
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
    resp = {"code": 3, "msg": "Unimplemented"}
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
