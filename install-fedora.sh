#!/bin/bash

echo "Uninstalling old docker"
sudo dnf remove docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-selinux \
                docker-engine-selinux \
                docker-engine

echo "Upgrading packages"
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager \
    --add-repo \
    https://download.docker.com/linux/fedora/docker-ce.repo

echo "Installing docker.."
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"

echo "Installing docker-compose"
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Adding user to docker group"
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart
sudo systemctl enable docker

echo "Installing docker-posbox"
sudo mkdir -p /posbox
sudo chown -R $USER:$USER /posbox
git clone https://github.com/AwesomeFoodCoops/docker-posbox.git /posbox/docker-posbox
cd /posbox/docker-posbox

echo "Building image"
sudo docker-compose build --pull
sudo docker-compose up -d
