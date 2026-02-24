## Making data

### Setup
See the instructions at the end to make sure synthea is set up

### Using Synthea

This is a three step process:

1. Generate data
2. Simulate data
3. Modify data

You can (this is just for example) generate data using
a command like (do not run) `./run_synthea -p 25` which
needs to be run in the sythea directory.

### Making our data

#### Breast Screening Data

We run Synthea to focus on breast screening.

It took some tweaking of the default modules to get the screening rates
to be high. I was getting 350 of 1000 patients to get screening with these
modifications (before these it was closer to 1 in 100). I would have
guessed these changes got it so 100% of patients were screened, but that was
not the case, still it is enough.


```
cd <synthea repo dir>

sed -i 's/"probability": 0.85/"probability": 1.0/g' src/main/resources/modules/breast_cancer.json
jq '.states.Female = {"type": "Simple", "direct_transition": "Pre_breastCancer", "remarks": ["Modified to send all women through screening"]}' ./src/main/resources/modules/breast_cancer.json > ./src/main/resources/modules/breast_cancer.json.tmp && mv ./src/main/resources/modules/breast_cancer.json.tmp ./src/main/resources/modules/breast_cancer.json
jq '.states["Age 39-59"].distributed_transition = [{"transition": "Breast Cancer Screening Due", "distribution": 1.0}]' ./src/main/resources/modules/breast_cancer.json > tmp.json && mv tmp.json ./src/main/resources/modules/breast_cancer.json
# Modify Age 60-69 (keep male logic, but send all females to screening)
jq '.states["Age 60-69"].complex_transition[1].distributions = [{"transition": "Breast Cancer Screening Due", "distribution": 1.0}]' ./src/main/resources/modules/breast_cancer.json > tmp.json && mv tmp.json ./src/main/resources/modules/breast_cancer.json
# Fix Age 0-39 (change to screening instead of symptoms)
jq '.states["Age 0-39"].direct_transition = "Breast Cancer Screening Due"' ./src/main/resources/modules/breast_cancer.json > tmp.json && mv tmp.json ./src/main/resources/modules/breast_cancer.json
# Fix Age 69-85 (send 100% to screening)
jq '.states["Age 69-85"].distributed_transition = [{"transition": "Breast Cancer Screening Due", "distribution": 1.0}]' ./src/main/resources/modules/breast_cancer.json > tmp.json && mv tmp.json ./src/main/resources/modules/breast_cancer.json
# Fix Age 85-140 (send 100% to screening)
jq '.states["Age 85-140"].distributed_transition = [{"transition": "Breast Cancer Screening Due", "distribution": 1.0}]' ./src/main/resources/modules/breast_cancer.json > tmp.json && mv tmp.json ./src/main/resources/modules/breast_cancer.json

./gradlew clean build
```


To be safe we clear the output directory before running.

We run a fully female population aged 40 to 70.

```
rm -rf output/*
./run_synthea -p 1002-s 67890 -g F -a 40-70 -m breast_cancer --exporter.fhir.export=true
```

This makes 1002 patients. The last 2 will be saved for audits, we'll rename
some for editing to introduce auditing failures.

```
mv ./output/fhir/Richelle340_Wiegand701_943fec3e-ac5a-2284-2b4f-ce652b6f09d3.json ./output/fhir/mod_Richelle340_Wiegand701_943fec3e-ac5a-2284-2b4f-ce652b6f09d3.json
mv ./output/fhir/Mazie442_Nicolasa738_Johns824_fb6f0e59-b567-5f68-5a9b-da07fef7370d.json ./output/fhir/mod_Mazie442_Nicolasa738_Johns824_fb6f0e59-b567-5f68-5a9b-da07fef7370d.json
mv ./output/fhir/Justine412_Garnett735_Schoen8_39b7de4b-abf2-d772-461e-193e503a035b.json ./output/fhir/mod_Justine412_Garnett735_Schoen8_39b7de4b-abf2-d772-461e-193e503a035b.json
```

These files were copied to the repo, with the mod files copied
temporarily to the ehr folder instead of ehr/output




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

