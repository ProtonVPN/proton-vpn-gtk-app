#!/bin/sh

echo "Every $1 seconds writes RSS mem usage of PID $2"
while true
do
        ps u --no-header --pid $2 | awk '{print $6}'
        sleep $1

done

