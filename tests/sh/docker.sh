#!/usr/bin/env bash

set -e

echo_bold() {
    echo "\033[1m${1}\033[0m"
}

ROOT_FOLDER=/home/raphael/PycharmProjects/md2nfv

PORT_A=8081
PORT_B=8082
PORT_C=8083
PORT_D=8084
PORT_E=8085

CONF_A=/home/cfgs/A.yaml
CONF_B=/home/cfgs/B.yaml
CONF_C=/home/cfgs/C.yaml
CONF_D=/home/cfgs/D.yaml
CONF_E=/home/cfgs/E.yaml

start_containers() {
    echo_bold "build docker image"

    cd ${ROOT_FOLDER}
    docker build -t nso:v1.0 .
    cd -

    echo_bold "starting docker containers"
    docker run --name mdoA -d nso:v3.0 -p 8080:${PORT_A} --env MDO_CONFIG=${CONF_A}
    docker run --name mdoB -d nso:v3.0 -p 8080:${PORT_B} --env MDO_CONFIG=${CONF_B}
    docker run --name mdoC -d nso:v3.0 -p 8080:${PORT_C} --env MDO_CONFIG=${CONF_C}
    docker run --name mdoD -d nso:v3.0 -p 8080:${PORT_D} --env MDO_CONFIG=${CONF_D}
    docker run --name mdoE -d nso:v3.0 -p 8080:${PORT_E} --env MDO_CONFIG=${CONF_E}
}

stop_containers() {

    echo_bold "stopping docker containers"
    docker stop mdoA
    docker stop mdoB
    docker stop mdoC
    docker stop mdoD
    docker stop mdoE

    echo_bold "removing docker containers"
    docker rm mdoA
    docker rm mdoB
    docker rm mdoC
    docker rm mdoD
    docker rm mdoE
}

CMD=$1

case "$CMD" in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    *)
        echo_bold "Usage: $0 [ start | stop ]"
        exit 1
esac
