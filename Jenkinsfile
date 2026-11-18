pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        timeout(time: 5, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
        skipDefaultCheckout(true)
    }
    triggers { githubPush() }
    environment {
        IMAGE_REPO = 'nash0017/devops-midterm-fa23-bds-056'
        STUDENT_ID = 'FA23-BDS-056'
        METRICS_URL = 'http://16.192.221.29:8000/metrics'
    }
    stages {
        stage('Checkout latest dataset') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(12)}"
                }
            }
        }
        stage('Build training environment') {
            steps { sh 'docker build --target tooling -t midterm-tooling:latest .' }
        }
        stage('Retrain from committed dataset') {
            steps {
                sh '''docker run --rm --user "$(id -u):$(id -g)" -e GIT_COMMIT="$GIT_COMMIT" -e HOME=/tmp -v "$WORKSPACE:/app" midterm-tooling:latest python train.py'''
            }
        }
        stage('Test API and model') {
            steps {
                sh '''docker run --rm --user "$(id -u):$(id -g)" -e GIT_COMMIT="$GIT_COMMIT" -e HOME=/tmp -v "$WORKSPACE:/app" midterm-tooling:latest pytest -q -p no:cacheprovider --junitxml=test-results.xml'''
            }
            post { always { junit allowEmptyResults: true, testResults: 'test-results.xml' } }
        }
        stage('Build image') {
            steps { sh 'docker build --target runtime -t "$IMAGE_REPO:$IMAGE_TAG" -t "$IMAGE_REPO:latest" .' }
        }
        stage('Deploy and verify') {
            steps {
                sh 'sh deploy.sh "$IMAGE_REPO:$IMAGE_TAG"'
                sh '''python3 -c 'import json,os,urllib.request; m=json.load(urllib.request.urlopen("http://127.0.0.1:8000/metrics")); assert m["git_sha"]==os.environ["GIT_COMMIT"]; assert m["student_id"]==os.environ["STUDENT_ID"]; print(m)' '''
            }
        }
        stage('Publish Docker Hub image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_TOKEN')]) {
                    sh '''
                        set +x
                        export DOCKER_CONFIG="$(mktemp -d)"
                        trap 'rm -rf "$DOCKER_CONFIG"' EXIT
                        printf '%s' "$DOCKER_TOKEN" | docker login --username "$DOCKER_USER" --password-stdin
                        docker push "$IMAGE_REPO:$IMAGE_TAG"
                        docker push "$IMAGE_REPO:latest"
                    '''
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/metrics.json'
            script { env.BUILD_RESULT = currentBuild.currentResult }
            withCredentials([usernamePassword(credentialsId: 'smtp-gmail', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASSWORD')]) {
                sh 'python3 notify_build.py'
            }
        }
    }
}
