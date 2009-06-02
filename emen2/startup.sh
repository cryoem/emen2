#!/bin/sh

PYTHONPATH=.. python -c "from emen2config import *;print EMEN2LOG"
PYTHONPATH=.. python -c "from emen2config import *;print EMEN2ERRLOG"
PYTHONPATH=.. python -c "from emen2config import *;print EMEN2JOBFILE"
PYTHONPATH=.. EMEN2ROOT=`python -c "from emen2config import *;print EMEN2ROOT"`
echo $EMEN2ROOT
PYTHONPATH=.. python -c "from emen2config import *;print PYTHONBIN"

PYTHONPATH=.. python $EMEN2ROOT/emen2control.py --start
