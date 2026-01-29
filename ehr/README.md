# Notes

## Hapi Server
I (CL) ran this on Ubuntu 24.04.2

Install docker
```
sudo apt update
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


## Making data

If you have java installed, jump down to synthea cloning

Run
```
java -version
```

I see this
```
openjdk version "17.0.17" 2025-10-21
OpenJDK Runtime Environment (build 17.0.17+10-Ubuntu-124.04)
OpenJDK 64-Bit Server VM (build 17.0.17+10-Ubuntu-124.04, mixed mode, sharing)
```

Version 17 is the best for Synthea, but 21 may work too

If not installed run
```
sudo apt update
sudo apt install openjdk-17-jdk -y
```

To clone synthea, run the following
```
git clone git@github.com:synthetichealth/synthea.git
# I was at commit 7187764
```

And run it using the RNG seed of 12345 for deterministic output

```
./run_synthea -p 25 -s 12345
```


```
for file in output/fhir/*.json; do
  echo "Uploading $file..."
  curl -X POST -H "Content-Type: application/fhir+json" \
       --data-binary "@$file" \
       http://localhost:8080/fhir
done
```


