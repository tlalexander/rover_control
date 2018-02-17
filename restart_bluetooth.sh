#!/bin/bash

sudo systemctl daemon-reload
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
