# docker-posbox
Docker PosBox image

# Usage

1. Clone this repository `git clone https://github.com/AwesomeFoodCoops/docker-posbox` && `cd docker-posbox`

2. Edit the docker-compose.yml `SERVER_WIDE_MODULES` arg according to your requirements.

3. Run
```
$ sudo docker-compose build --pull
$ sudo docker-compose up
```

4. Try to access: `http://localhost:8069/hw_proxy/status`. You should see the hw proxy status page.
