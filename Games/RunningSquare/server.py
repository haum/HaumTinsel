#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import serial
import threading
import pickle
from time import sleep
from datetime import datetime
from bottle import route, run, request, redirect, static_file
import pygal
from pygal.style import Style

STATIC_ROOT="static/"
BASE_ADDR="http://localhost:8080/"
SERIAL_IFACE="/dev/ttyUSB0"
FIFO="fifo_bridge"
HISTORY="flakes_history.pickle"

class FlakeAdder(threading.Thread):

    def __init__(self, iface=SERIAL_IFACE):
        threading.Thread.__init__(self)

        self.iface = iface
        self.conn = serial.Serial(self.iface, 115200)
        self.stop_gracefully = False
        self.flakes_history = {
		0: [], 1:[], 2:[], 3:[],
		'dates':[],
		'gamedata':''
	}

    def quit(self):
        self.stop_gracefully = True

    def renew_conn(self):
        try:
            self.conn.close()
        finally:
            self.conn = serial.Serial(self.iface, 115200)

    def process_tinsel_values(self, values):
        self.flakes_history[0].append(values.count('0'))
        self.flakes_history[1].append(values.count('1'))
        self.flakes_history[2].append(values.count('2'))
        self.flakes_history[3].append(values.count('3'))
        self.flakes_history['dates'].append(datetime.now())
        self.flakes_history['gamedata'] = values
        line_chart = pygal.Line(style=Style(colors=('#ffff00', '#ff00ff', '#00ffff', '#ff0000')))
        line_chart.title = u'Évolution de la couleur des flocons'
        line_chart.add('', self.flakes_history[0])
        line_chart.add('', self.flakes_history[1])
        line_chart.add('', self.flakes_history[2])
        line_chart.add('', self.flakes_history[3])
        line_chart.render_to_file(STATIC_ROOT+'chart.svg')

    def run(self):
	try:
            with open(HISTORY, 'r') as f:
                self.flakes_history = pickle.loads(f.read())
	except IOError:
            pass
	self.conn.write('\nR' + self.flakes_history['gamedata'] + '\n')
        with open(FIFO,'r') as f:
            while not self.stop_gracefully:
#                try:
                    code = str(f.readline()).strip()
                    if code == 'S':
                        self.conn.write('S')
                        self.process_tinsel_values(self.conn.readline())
                    elif code:
                        self.conn.write(code + '\n')
                        print code
                    sleep(0.3)
#                except:
#                    self.renew_conn()
        with open(HISTORY, 'w') as f:
            f.write(pickle.dumps(self.flakes_history))
        print 'Gracefully stopped'

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
#    if BASE_ADDR != request.headers.get('Referer'):
#        # do not try to cheat... the redirect is permanent
#        return redirect('http://haum.org', code=301)
#    else:
        add_flake(code)
        return {'status': 'ok'}

if __name__=='__main__':
    with open('pid', 'w') as f:
        f.write(str(os.getpid()))
    try:
        os.mkfifo(FIFO)
    except OSError:
        pass
    t = FlakeAdder()
    t.start()
    run(host='0.0.0.0', port=8080)
    t.quit()
    open(FIFO, 'a') # Generate FIFO event to stop t
    t.join()
    os.unlink(FIFO)
    os.unlink('pid')
