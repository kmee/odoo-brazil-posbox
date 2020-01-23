#!/bin/bash

sudo apt install -y docker docker-compose
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart

