#!/usr/bin/env bash

ETH_FOLDER=/home/raphael/PycharmProjects/md2nfv/chains/

byobu new-session -d -s "ethereum" "cd ${ETH_FOLDER}/A && ./start.sh"
byobu new-window "cd ${ETH_FOLDER}/B && ./start.sh"
byobu new-window "cd ${ETH_FOLDER}/C && ./start.sh"
byobu new-window "cd ${ETH_FOLDER}/D && ./start.sh"
byobu new-window "cd ${ETH_FOLDER}/E && ./start.sh"
