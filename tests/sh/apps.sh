#!/usr/bin/env bash

ROOT_FOLDER=/home/raphael/PycharmProjects/md2nfv
ETH_FOLDER=/home/raphael/PycharmProjects/md2nfv/chains/

CONF_A=/cfgs/A.yaml
CONF_B=/cfgs/B.yaml
CONF_C=/cfgs/C.yaml
CONF_D=/cfgs/D.yaml
CONF_E=/cfgs/E.yaml

byobu new-session -d -s "apps" "cd ${ETH_FOLDER}/A && exchange_app --configs ${ROOT_FOLDER}/${CONF_A} --debug true"
byobu new-window "cd ${ETH_FOLDER}/B && exchange_app --configs ${ROOT_FOLDER}/${CONF_B} --debug true"
byobu new-window "cd ${ETH_FOLDER}/C && exchange_app --configs ${ROOT_FOLDER}/${CONF_C} --debug true"
byobu new-window "cd ${ETH_FOLDER}/D && exchange_app --configs ${ROOT_FOLDER}/${CONF_D} --debug true"
byobu new-window "cd ${ETH_FOLDER}/E && exchange_app --configs ${ROOT_FOLDER}/${CONF_E} --debug true"

