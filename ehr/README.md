# Notes

I (CL) ran this on Ubuntu 24.04.2

Install docker
```
sudo apt install -y docker-compose
``

See the version
```
docker-compose version
```

My output - it does not have to match your's, but if
there are issues, this is a possible reason

```
docker-compose version 1.29.2, build unknown
docker-py version: 5.0.3
CPython version: 3.12.3
OpenSSL version: OpenSSL 3.0.13 30 Jan 2024
```

Get docker running Postgres and the Hapi FHIR server
```
sudo docker-compose up -d
```

Test it out, run this on your host machine

```
curl -X GET "http://localhost:8080/fhir/metadata"
```


