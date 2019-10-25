# docker-posbox
Docker PosBox image

# Usage

Configure the docker-compose.yml `SERVER_WIDE_MODULES` arg according to your requirements.

`$ docker-compose build --pull`

`$ docker-compose up`

Test to access: `https://localhost:8069/hw_proxy/status`. You should see the hw proxy status page.
