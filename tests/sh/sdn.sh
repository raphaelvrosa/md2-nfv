#!/usr/bin/env bash


RYU_FOLDER=/home/raphael/PycharmProjects/md2nfv/ofdp/
MN_FOLDER=/home/raphael/PycharmProjects/md2nfv/mn/

PORT_A=6633
PORT_B=6634
PORT_C=6635
PORT_D=6636
PORT_E=6637

PORT_NSO_A=8891
PORT_NSO_B=8892
PORT_NSO_C=8893
PORT_NSO_D=8894
PORT_NSO_E=8895

WS_ADDR=0.0.0.0

byobu new-session -d -s "sdn" "cd ${MN_FOLDER} && mn -c && python ./topo.py"
sleep 10
byobu new-window  "cd ${RYU_FOLDER} && ryu-manager --wsapi-host ${WS_ADDR} --wsapi-port ${PORT_NSO_A} --ofp-tcp-listen-port ${PORT_A} --default-log-level 1 rest_qos.py  ryu.app.rest_conf_switch"
byobu new-window  "cd ${RYU_FOLDER} && ryu-manager --wsapi-host ${WS_ADDR} --wsapi-port ${PORT_NSO_B} --ofp-tcp-listen-port ${PORT_B} --default-log-level 1 rest_qos.py  ryu.app.rest_conf_switch"
byobu new-window  "cd ${RYU_FOLDER} && ryu-manager --wsapi-host ${WS_ADDR} --wsapi-port ${PORT_NSO_C} --ofp-tcp-listen-port ${PORT_C} --default-log-level 1 rest_qos.py  ryu.app.rest_conf_switch"
byobu new-window  "cd ${RYU_FOLDER} && ryu-manager --wsapi-host ${WS_ADDR} --wsapi-port ${PORT_NSO_D} --ofp-tcp-listen-port ${PORT_D} --default-log-level 1 rest_qos.py  ryu.app.rest_conf_switch"
byobu new-window  "cd ${RYU_FOLDER} && ryu-manager --wsapi-host ${WS_ADDR} --wsapi-port ${PORT_NSO_E} --ofp-tcp-listen-port ${PORT_E} --default-log-level 1 rest_qos.py  ryu.app.rest_conf_switch"


ovs-vsctl set-manager ptcp:6632

sleep 5

curl -X PUT -d '"tcp:127.0.0.1:6632"' http://localhost:${PORT_NSO_A}/v1.0/conf/switches/0000000000000001/ovsdb_addr
curl -X PUT -d '"tcp:127.0.0.1:6632"' http://localhost:${PORT_NSO_B}/v1.0/conf/switches/0000000000000002/ovsdb_addr
curl -X PUT -d '"tcp:127.0.0.1:6632"' http://localhost:${PORT_NSO_C}/v1.0/conf/switches/0000000000000003/ovsdb_addr
curl -X PUT -d '"tcp:127.0.0.1:6632"' http://localhost:${PORT_NSO_D}/v1.0/conf/switches/0000000000000004/ovsdb_addr
curl -X PUT -d '"tcp:127.0.0.1:6632"' http://localhost:${PORT_NSO_E}/v1.0/conf/switches/0000000000000005/ovsdb_addr

