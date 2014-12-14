#!/bin/bash

pid=$(cat pid)
kill $pid
rm pid
rm fifo_bridge
