# Notes

Run the docker compose up --build command as described in the
top level README - this will create the Hapi FHIR server. Note
that it took several minutes without any output before the
server became available

To test the server is running, execute the following:

```
curl -X GET "http://localhost:8080/fhir/metadata"
```


## Making data

### Using Synthea

This is a two step process:

1. Generate data
2. Upload data

We go to the synthea directory and run it using the RNG seed of
12345 to get a deterministic output

```
./run_synthea -p 25 -s 12345
```

This generates files in ./output/fhir. I (CL) have synthea located
in ~/src/synthea so data is in ~/src/synthea/output/fhir

Verify you have a `hospitalInformation1769758307877.json` - if so,
your data maches mine (CL)

Navigate back to the directory with this README and run

```
./upload_fhir.sh <path/to/output/fhir/dir>

# For example
./upload_fhir.sh ~/src/synthea/output/fhir
```


### See some data

Run this curl to find a patient to get data for (you can remove the `| jq ...` to see the patient object)

```
curl -s "http://localhost:9080/fhir/Patient?_count=1&_pretty=true" | jq '.entry[0].resource.id'
```

Take the output from that, I got 26171, and put it into the URL below to retrieve the full patient chart:

```
curl "http://localhost:9080/fhir/Patient/26171/\$everything?_pretty=true"
```



### Pre-reqs

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

