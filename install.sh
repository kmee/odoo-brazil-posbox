#!/bin/bash

echo "Installing docker.."
sudo apt update && sudo apt upgrade
sudo apt install -y docker docker-compose
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart

echo "Installing docker-posbox"
sudo mkdir -p /posbox && chown -R $USER:$USER /posbox
git clone https://github.com/AwesomeFoodCoops/docker-posbox.git /posbox/docker-posbox
cd /posbox/docker-posbox

echo "Building image"
sudo docker-compose build --pull
