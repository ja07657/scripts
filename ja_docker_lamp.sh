#!/bin/bash
docker run -d -p 81:80 -p 3306:3306 -p 444:443 -v /app:/var/www/html \
-e MYSQL_PASS=mypass dell/lamp
docker ps
