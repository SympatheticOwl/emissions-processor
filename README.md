# UIUC CS437 IoT Lab 4

## Requirements

---
### firehose.py
* run the following command in the directory where firehose.py is stored to install dependencies
```shell
pip3 install boto3 awsiotsdk -t .
```
* run this command to zip the file and its deps then upload to your artifact bucket
```shell
zip -r ../firehose.zip * && cd .. && aws s3 cp firehose.zip s3://${ARTIFACT_BUCKET}/artifacts/com.emission.firehose/${FIREHOSE_COMPONENT_VERSION}/
```
---
### process_emission.py
* run the following command in the directory where process_emission.py is stored to install dependencies
```shell
pip3 install greengrasssdk awsiotsdk -t .
```
* run this command to zip the file and its deps then upload to your artifact bucket
```shell
zip -r ../emission_processor.zip * && cd .. && aws s3 cp emission_processor.zip s3://${ARTIFACT_BUCKET}/artifacts/com.emission.processor/${EMISSIONS_COMPONENT_VERSION}/
```
---
### emulator_client.py, emulator_client_v2.py, and create_thing_cert.py
```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install boto3 AWSIoTPythonSDK pandas 
```
---
### emissions_visualization.ipynb
```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install pandas matplotlib seaborn numpy pyathena
```