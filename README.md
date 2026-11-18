# DevOps Lab Midterm FA23-BDS-056

Nashama Asim · CSC418 DevOps for Cloud Computing · Fall 2026

## Links

- Repository: https://github.com/Nash0017/devops-midterm-fa23-bds-056
- Pipeline source: [Jenkinsfile](Jenkinsfile)
- Public metrics through the temporary EC2 tunnel: https://involvement-genealogy-hay-jackson.trycloudflare.com/metrics
- Intended direct EC2 metrics address: http://16.192.221.29:8000/metrics (AWS security-group access is still required)
- Docker Hub image: `nash0017/devops-midterm-fa23-bds-056:latest`
- Jenkins job: `MIDTERM-FA23-BDS-056`
- Build email sender: `nashama123asim@gmail.com`

## Workload

The assigned telecom configuration uses seed 31832 and the features `signal_noise`, `user_density`, `tower_temperature`, and `handoff_count`. The initial CSV contains 300 generated rows. The training script preserves the supplied logistic regression, imputation, scaling, stratified evaluation, and production retraining logic.

## Pipeline

A GitHub push triggers Jenkins. Jenkins checks out the exact commit, builds the cached Python 3.12 tooling image, retrains from the committed CSV, runs four model and API tests, builds the deployment image, checks a candidate container, deploys on port 8000, verifies the deployed commit, and publishes versioned and latest Docker Hub tags. The post-build step sends Gmail SMTP notifications on success or failure.

Dataset generation runs only for initial setup. Jenkins does not regenerate the CSV, so grader additions are retained.

## Jenkins credentials

Create these two global Username with password credentials:

| ID | Username | Password field |
| --- | --- | --- |
| `dockerhub` | `nash0017` | Docker Hub token with repository write permission |
| `smtp-gmail` | `nashama123asim@gmail.com` | Gmail app password |

Do not commit credentials, private keys, or app passwords.

## Networking

The FastAPI container listens on EC2 port 8000. The AWS instance has no IAM role, and inbound AWS security-group changes require account access. A temporary Cloudflare tunnel provides public API access and signed GitHub webhook forwarding. Its URL can change if the tunnel process restarts; update the webhook and submitted URL if that happens. Jenkins administrative pages remain available through an SSH tunnel.

The public webhook path is `/github-webhook/`. A separate EC2 gateway verifies its SHA-256 HMAC before forwarding it to Jenkins. The webhook secret is stored outside this repository.

## Manual verification on EC2

```bash
curl http://127.0.0.1:8000/metrics
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"records":[{"signal_noise":0.1,"user_density":0.2,"tower_temperature":0.3,"handoff_count":0.4}]}'
docker ps --filter name=midterm-api
```

SMTP acceptance confirms sending, not delivery into the instructor inbox. Verify actual receipt and webhook-triggered redeployment before submission.
