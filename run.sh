#!/bin/bash

cd "$(dirname "$0")"
exec $VIRTUAL_ENV/bin/gunicorn -w 1 -b 127.0.0.1:8889 --log-level debug --access-logfile - --error-logfile - app:app
