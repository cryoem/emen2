#!/bin/sh

EMEN2LOG=`python -c "from emen2config import *;print EMEN2LOG"`
EMEN2ERRLOG=`python -c "from emen2config import *;print EMEN2ERRLOG"`
EMEN2JOBFILE=`python -c "from emen2config import *;print EMEN2JOBFILE"`
EMEN2ROOT=`python -c "from emen2config import *;print EMEN2ROOT"`
PYTHONBIN=`python -c "from emen2config import *;print PYTHONBIN"`


python2.4 $EMEN2ROOT/TwistServer.py >> $EMEN2LOG 2>> $EMEN2ERRLOG &
echo $! > $EMEN2JOBFILE
disown %1
