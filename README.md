# DevOps Lab Midterm FA23-BDS-056

Nashama Asim · CSC418 DevOps for Cloud Computing · Fall 2026

## Links

- Repository: https://github.com/Nash0017/devops-midterm-fa23-bds-056
- Pipeline source: [Jenkinsfile](Jenkinsfile)
- Public EC2 metrics: http://16.192.221.29:8000/metrics
- Intended direct EC2 metrics address: http://16.192.221.29:8000/metrics
- Docker Hub image: `nash0017/devops-midterm-fa23-bds-056:latest`
- Jenkins job: `MIDTERM-FA23-BDS-056`
- Build email sender: `nashama123asim@gmail.com`

## Workload

The assigned telecom configuration uses seed 31832 and the features `signal_noise`, `user_density`, `tower_temperature`, and `handoff_count`. The initial CSV contains 300 generated rows. The training script preserves the supplied logistic regression, imputation, scaling, stratified evaluation, and production retraining logic.

## Pipeline

A GitHub push triggers Jenkins, with one-minute SCM polling as a fallback for missed events. Jenkins checks out the exact commit, builds the cached Python 3.12 tooling image, retrains from the committed CSV, runs four model and API tests, builds the deployment image, checks a candidate container, and deploys on port 8000. A separate verifier independently recomputes evaluation accuracy and predictions, then checks the served commit, dataset byte digest, row count, and model version. Jenkins publishes build-number, full-commit, and latest Docker Hub tags. Notifications are sent from `nashama123asim@gmail.com` to `qasimalik@gmail.com`, with the student sender copied, on success or failure.

Dataset generation runs only for initial setup. Jenkins does not regenerate the CSV, so grader additions are retained.

## Jenkins credentials

Create these two global Username with password credentials:

| ID | Username | Password field |
| --- | --- | --- |
| `dockerhub` | `nash0017` | Docker Hub token with repository write permission |
| `smtp-gmail` | `nashama123asim@gmail.com` | Gmail app password |

Do not commit credentials, private keys, or app passwords.

## Networking

The FastAPI container listens on EC2 port 8000. The AWS security group permits public API requests on port 8000 and signed webhook requests on port 8081. The public webhook is http://16.192.221.29:8081/github-webhook/. Jenkins administrative pages remain available through an SSH tunnel.

The public webhook path is `/github-webhook/`. A separate EC2 gateway verifies its SHA-256 HMAC before forwarding it to Jenkins. The webhook secret is stored outside this repository.

## Manual verification on EC2

```bash
curl http://127.0.0.1:8000/metrics
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"records":[{"signal_noise":0.1,"user_density":0.2,"tower_temperature":0.3,"handoff_count":0.4}]}'
docker ps --filter name=midterm-api
```

SMTP acceptance confirms sending, not receipt in the grading inbox. Verify actual receipt and webhook-triggered redeployment before submission.

## Java update recovery

An unattended Java upgrade on 20 November replaced the process-spawn helper while Jenkins was still running, causing Git checkout to fail before the pipeline could start. Restarting Jenkins repairs that mismatch. The installed systemd drop-in in `ops/jenkins-process-launch.conf` uses the FORK launch mechanism so child process creation does not depend on that on-disk helper. Java updates remain enabled. Restart Jenkins after Java upgrades as recommended by Jenkins.

## Independent verification

The pipeline runs `verify_deployment.py` in a separate process. It does not call `train.py` or trust the model's own reported accuracy: it reconstructs the specified imputation, scaling, stratified evaluation split, and logistic regression, then compares the running API against those results. Proof is archived as `artifacts/verification.json` and attached to the notification.
