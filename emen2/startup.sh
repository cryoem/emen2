#!/bin/sh
EMEN2LOG=`python -c "from emen2.emen2config import *;print g.EMEN2LOG"`
EMEN2ERRLOG=`python -c "from emen2.emen2config import *;print g.EMEN2ERRLOG"`
EMEN2JOBFILE=`python -c "from emen2.emen2config import *;print g.EMEN2JOBFILE"`
EMEN2ROOT=`python -c "from emen2.emen2config import *;print g.EMEN2ROOT"`
PYTHONBIN=`python -c "from emen2.emen2config import *;print g.PYTHONBIN"`


python $EMEN2ROOT/TwistServer.py >> $EMEN2LOG 2>> $EMEN2ERRLOG &
echo $! > $EMEN2JOBFILE
disown %1
