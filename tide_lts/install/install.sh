#!/usr/bin/env bash

echo "installing tide_lts ..."
cp -v tide_lts.sh /usr/bin/tide_lts
cp -v ../main.py /usr/bin/tide_lts

echo "creating the tide_lts service ..."
cp -v tide_lts.service /etc/systemd/system
chmod -v +x /usr/bin/tide_lts

echo "adding tide_lts to startup services ..."
sudo systemctl enable tide_lts

echo "starting tide_lts service ..."
sudo systemctl start tide_lts
