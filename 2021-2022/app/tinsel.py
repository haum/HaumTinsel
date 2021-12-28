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

cube_data = [0]*64
for i in range(64):
    cube_data[i] = choice(list(colors.keys()))

def anim():
    global cube_data

    delay = 1.0/30
    autoplay = 0
    anim = 0

    while True:
        if autoplay <= 0:
            autoplay = 15*60/delay
            cube_data[0] = choice(list(colors.keys()))
        autoplay -= 1
        anim += 0.5*delay
        anim %= 1.0 + 0.5*delay
        for i in range(64):
            r = 0.4*i % 0.5
            a = min(max(0, (anim - r)*2), 1)
            c1 = colors[cube_data[i-1]]
            c2 = colors[cube_data[i]]
            c = (int(c1[0]*a + c2[0] * (1-a)),
                 int(c1[1]*a + c2[1] * (1-a)),
                 int(c1[2]*a + c2[2] * (1-a)))
            tals[i] = c
        if anim >= 0.999:
            cube_data = cube_data[-1:] + cube_data[:-1]
        tals.leds.blit()
        time.sleep(delay)

class TinselHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/add/0', '/add/1', '/add/2', '/add/3']:
            col = self.path[-1]
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            cube_data[0] = col
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)

with socketserver.TCPServer(("", 8000), TinselHandler) as httpd:
    t = threading.Thread(target=anim)
    t.start()
    httpd.serve_forever()
