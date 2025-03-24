#!/bin/bash

if [[ -n "$@" ]]; then
  /usr/bin/logger -t sd-notifier "${0} invoked with ${@}"
else
  /usr/bin/logger -t sd-notifier "${0} invoked with no arguments"
fi
