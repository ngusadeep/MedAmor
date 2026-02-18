# EHR Test System

This is a test FHIR server that mimicks an EHR system.

As part of this system, we have data that can be loaded into the EHR so the
server can act as a live EHR.

## Running

Make sure you have docker compose v2 installed. See notes in the MedArmor
README for details.

The HAPI FHIR service (different app) is behind profiles and does not start by
default, but can be started using the following:

```bash
docker compose --profile hapi up --build
```

Note that it can take several minutes without any output before the server
becomes available.

To test the server is running, run the following:

```
curl -X GET "http://localhost:9080/fhir/metadata"
```

Additional management commands are below.


## Loading Data

We have data prepared to load into the system. If you wish to make this data
yourself or make it in a different way, see <data_notes.md>.


## Uploading Data

```
./upload_fhir.sh data/breast/fhir/
```

## Other Management Notes

### See some data

Run this curl to find a patient to get data for (you can remove the
`| jq ...` to see the patient object):

```
curl -s "http://localhost:9080/fhir/Patient?_count=1&_pretty=true" | jq '.entry[0].resource.id'
```

Take the output from that, I got 26171, and put it into the URL below to
retrieve the full patient chart:

```
curl "http://localhost:9080/fhir/Patient/26171/\$everything?_pretty=true"
```

You may also use the interactive browser in the
`orchestrator/interactive_fhir_browser` (see the README there).

### Taking the server down

```
sudo docker compose down
```

### Resetting the DB

First take the server down, then run the following:

```
sudo docker volume rm medaudit_hapi_db_data
```
