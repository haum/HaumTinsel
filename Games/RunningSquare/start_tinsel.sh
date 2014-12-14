#!/bin/bash

mkfifo fifo_bridge
python server.py&
echo $! > pid
