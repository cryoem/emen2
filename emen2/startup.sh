#!/bin/sh

python /home/emen2/EMEN2/emen2/TwistServer.py >/tmp/emen2log 2>/tmp/emen2errlog &
echo $! >/tmp/emen2job
disown %1
