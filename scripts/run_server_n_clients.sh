#!/usr/bin/env bash
echo "Running Server and Multiple Clients"
count=0
cd ..
while [ $count -lt $1 ]
do
    grep python3 client.py & >> log.txt
    ((count++))
done
python3 server.py
