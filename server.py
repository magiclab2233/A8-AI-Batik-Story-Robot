import datetime
import jwt
from threading import Thread
from play import *

# 配置密钥
iss = "wanghuitest-jwt-20250305"
secret ="9bd63a978e68d58d0906073aa0ae3422"

# 生成 JWT Token
def gen_token(exp=60*60, nbf=-10):
    return jwt.encode(
        {
            "iss": iss,
            "exp": get_timestamp(exp),
            "nbf": get_timestamp(nbf),
        },
        secret,
    )

def get_timestamp(delta_seconds):
    return datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        seconds=delta_seconds
    )

from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
@app.route('/token', methods=['GET'])
def getToken():
    token = gen_token()
    return jsonify({"token":token})

@app.route('/started',methods=['GET'])
def startedClient():
    print("start client")
    play_audio()
    return jsonify({"state":"started"})

@app.route('/closed',methods=['GET'])
def closeClient():
    print("close client")
    stop_browser()
    play_audio()
    return jsonify({"state":"closed"})

if __name__ == '__main__':
    import importlib.util

    file_path = "/home/pi/sensestorm3-rcu/src/rcu.py"
    module_name = "my_module"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fan_func = getattr(module, "set_fan_speed")
    fan_func(0)
    print("close fan")

    t = Thread(target=monitor, daemon=True)  # daemon=True 让线程随主程序退出
    t.start()

    app.run(debug=False,port=8000)
