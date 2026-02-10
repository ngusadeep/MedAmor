# Notes

Run the docker compose up --build command as described in the
top level README - this will create the Hapi FHIR server. Note
that it took several minutes without any output before the
server became available

If you are just working on building data, you can skip
running the full stack and just run the EHR:

```
sudo docker compose up hapi_fhir hapi_db
```


To test the server is running, execute the following:

```
curl -X GET "http://localhost:9080/fhir/metadata"
```


## Making data

Data was made using the notes in <data_notes.md>

There is no need to actually make this data

## Uploading data

```
./upload_fhir.sh data/breast/fhir/
```




## See some data

Run this curl to find a patient to get data for (you can remove the `| jq ...` to see the patient object)

```
curl -s "http://localhost:9080/fhir/Patient?_count=1&_pretty=true" | jq '.entry[0].resource.id'
```

Take the output from that, I got 26171, and put it into the URL below to retrieve the full patient chart:

```
curl "http://localhost:9080/fhir/Patient/26171/\$everything?_pretty=true"
```

You may also use the interactive browser in the `orchestrator/interactive_fhir_browser` (see the README there)

