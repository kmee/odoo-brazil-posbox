#!/usr/bin/env bash
set -e -x
git submodule init
git submodule update
virtualenv sandbox --system-site-packages --no-setuptools --no-pip
sandbox/bin/python <(curl https://bootstrap.pypa.io/get-pip.py) --upgrade setuptools==33.1.1 pip zc.buildout
./sandbox/bin/buildout "$@"
echo "Execute o buildout com seu arquivo de configuracao"
echo "Exemplo bin/buildout -c dev.cfg"

