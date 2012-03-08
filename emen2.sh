#!/bin/sh
#
#  Startup script for a Twisted service.
#
#  description: Start-up script for the Twisted service "emen2".

EMEN2DBHOME=/Users/irees/data/db.ncmi
rundir=$EMEN2DBHOME
pidfile=$rundir/applog/emen2.pid
logfile=$rundir/applog/emen2.log

PATH=/usr/bin:/bin:/usr/sbin:/sbin


case "$1" in
	start)
		echo "Starting emen2: twistd"
		twistd \
			--pidfile=$pidfile \
			--logfile=$logfile \
			--rundir=$rundir \
			emen2 -h $EMEN2DBHOME -e default,em,eman2,site				
		;;

	stop)
		if [ -f $pidfile ] 
		then
			echo "Stopping emen2: twistd"
			kill `cat "${pidfile}"`
		fi
		;;

	restart)
		"${0}" stop
		"${0}" start
		;;

    *)
		echo "Usage: ${0} {start|stop|restart|}" >&2
		exit 1
		;;
esac

exit 0