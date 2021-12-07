#!/usr/bin/env python

import http.server
import socketserver
import threading
import time
from random import choice

from controllers import TalController

tals = TalController()
colors = {
        '0': (255, 255, 0),
        '1': (0, 255, 255),
        '2': (255, 0, 255),
        '3': (255, 0, 0),
}

for i in range(64):
    tals[i] = colors[choice(list(colors.keys()))]

def anim():
    while True:
        tals.leds.chans = tals.leds.chans[-9:] + tals.leds.chans[:-9]
        tals.leds.blit()
        time.sleep(0.5)

class TinselHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/add/0', '/add/1', '/add/2', '/add/3']:
            col = self.path[-1]
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            tals[0] = colors[col]
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)

with socketserver.TCPServer(("", 8000), TinselHandler) as httpd:
    t = threading.Thread(target=anim)
    t.start()
    httpd.serve_forever()
