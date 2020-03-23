#!/usr/bin/env bash

set -e

if [ "$EUID" != "0" ]; then
  echo "You must be root to run this script."
  exit 1
fi

start_env() {
    my_dir="$(dirname "$0")"
    "${my_dir}/sdn.sh"
    "${my_dir}/eth.sh"
    "${my_dir}/apps.sh"
}

stop_env(){
    byobu kill-server
}


CMD=$1

case "$CMD" in
    start)
        start_env
        ;;
    stop)
        stop_env
        ;;
    *)
        echo_bold "Usage: $0 [ start | stop ]"
        exit 1
esac


