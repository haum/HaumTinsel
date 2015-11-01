#!/bin/bash

kill -INT $(cat pid) # Has to run in foreground to quit gracefully :-/
