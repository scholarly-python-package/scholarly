#!/bin/bash

tor_password="scholarly_password"
hashed_password=$(tor --hash-password $tor_password)
echo "ControlPort 9051" | sudo tee /etc/tor/torrc
echo "HashedControlPassword $hashed_password" | sudo tee -a /etc/tor/torrc

sudo service tor stop

sudo service tor start