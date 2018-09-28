from time import time
from uuid import uuid4
import os
#from urllib.parse import urlparse
from flask import Flask,jsonify,request

app = Flask(__name__,static_url_path='')
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/loadgbabios')
def loadgbabios():
    with open('static/roms/gba_bios.bin','rb') as f:
        resp = {'data':[i for i in f.read()]}
        #print(resp)
        return jsonify(resp)
        #return HttpResponse(f.read(),content_type='application/octet-stream')

if __name__ == '__main__':
    os.popen("explorer http://127.0.0.1:8000")
    app.run(host='0.0.0.0',port=8000)
