#!/usr/bin/env bash

echo "installing tide_lts ..."
mkdir -v /usr/bin/tide_lts
cp -v tide_lts.sh /usr/bin/tide_lts/
cp -v ../main.py /usr/bin/tide_lts/

echo "creating the tide_lts service ..."
cp -v tide_lts.service /etc/systemd/system
chmod -v +x /usr/bin/tide_lts/tide_lts.sh
chmod -v +x /usr/bin/tide_lts/main.py

echo "adding tide_lts to startup services ..."
sudo systemctl -v enable tide_lts

echo "starting tide_lts service ..."
sudo systemctl -v start tide_lts
