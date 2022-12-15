#!/usr/bin/env bash

if [ "${1}" == "rest" ]; then
  ./populate_cache.py
  ./rest.py
elif [ "${1}" == "populate" ]; then
  ./populate_cache.py -f
else
  /usr/bin/env bash "$@"
fi

