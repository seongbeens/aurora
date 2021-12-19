#!/bin/bash
cd /home/ubuntu/aurora-lastest

while true; do
	ISRUN=`pgrep -f "sudo python3 app.py" | wc -l`
	if [ ${ISRUN} -eq 0 ]; then
		nohup sudo python3 app.py > logs/nohup_app.out &
	fi

	ISRUN=`pgrep -f "sudo python3 schedules.py" | wc -l`
	if [ ${ISRUN} -eq 0 ]; then
		nohup sudo python3 schedules.py > logs/nohup_schedules.out &
	fi
	sleep 2
done