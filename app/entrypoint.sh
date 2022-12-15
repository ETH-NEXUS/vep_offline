#!/usr/bin/env bash

./populate_cache.py

if [ "${1}" == "rest" ]; then
  ./rest.py
elif [ "${1}" == "populate" ]; then
  ./populate_cache.py -f
else
  /usr/bin/env bash "$@"
fi

