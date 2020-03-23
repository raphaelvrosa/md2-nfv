#!/usr/bin/env bash

echo_bold() {
    echo -e "\033[1m${1}\033[0m"
}

kill_process_tree() {
    top=$1
    pid=$2

    children=`ps -o pid --no-headers --ppid ${pid}`

    for child in $children
    do
        kill_process_tree 0 $child
    done

    if [ $top -eq 0 ]; then
        kill -9 $pid &> /dev/null
    fi
}

reset() {
    init=$1;
    if [ $init -eq 1 ]; then
        echo_bold "-> Starting";
    else
        echo_bold "-> Stopping child processes...";
        kill_process_tree 1 $$
    fi
}

reset 1


#nso_app --configs /home/raphael/PycharmProjects/md2nfv/cfgs/A.yaml --debug true > mock_vnfm.log 2>&1 &
#sleep 5

#python nso_mock_server.py > mock_server.log 2>&1 &

python nso_test.py

sleep 5

#NSO_PID=`ps -o pid --no-headers -C nso_app`
#kill_process_tree 0 $NSO_PID


reset 0