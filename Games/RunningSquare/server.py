#!/usr/bin/env python

import serial
import threading
from time import sleep
from bottle import route, run, request, redirect, static_file

STATIC_ROOT="static/"
BASE_ADDR="http://localhost:8080/"
SERIAL_IFACE="/dev/ttyUSB0"
FIFO="fifo_bridge"

class FlakeAdder(threading.Thread):

    def __init__(self, iface=SERIAL_IFACE):
        threading.Thread.__init__(self)

        self.iface = iface
        self.conn = serial.Serial(self.iface, 115200)

    def renew_conn(self):
        try:
            self.conn.close()
        finally:
            self.conn = serial.Serial(self.iface, 115200)


    def run(self):
        with open(FIFO,'r') as f:
            while True:
#                try:
                    code = str(f.readline()).strip()
                    if code:
                        self.conn.write(code + '\n')
                        print code
                    sleep(0.3)
#                except:
#                    self.renew_conn()

@route('/static/<f:path>')
def static(f):
    return static_file(f, root=STATIC_ROOT)

def add_flake(code):
    with open(FIFO, 'a') as f:
        f.write(str(code)+'\n')

@route('/')
def home():
    return static('index.html')

@route('/add/<code:int>')
def game_win(code):
    if BASE_ADDR != request.headers.get('Referer'):
        # do not try to cheat... the redirect is permanent
        return redirect('http://haum.org', code=301)
    else:
        add_flake(code)
        return {'status': 'ok'}

if __name__=='__main__':
    t = FlakeAdder()
    t.start()
    run(host='0.0.0.0', port=8080)

