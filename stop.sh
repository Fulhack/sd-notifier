#!/bin/bash

if [[ -n "$@" ]]; then
  /usr/bin/logger -t sd-notifier "${0} invoked with ${@}"
else
  /usr/bin/logger -t sd-notifier "${0} invoked with no arguments"
fi

if [[ "${@}" =~ "sleep" ]]; then
  for ((i = 0; i < 10; i++)); do
    echo "$i"
    sleep 1
  done
fi
