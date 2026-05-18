pipeline {
    agent any

    parameters {
        string(name: 'HARBOR_HOST', defaultValue: 'localhost:5000', description: 'Adresse Harbor ou registry compatible')
        string(name: 'IMAGE_NAME', defaultValue: 'spam-detector/spam-api', description: 'Nom de l image')
        booleanParam(name: 'PUSH_TO_HARBOR', defaultValue: false, description: 'Pousser l image vers Harbor')
        booleanParam(name: 'HARBOR_LOGIN', defaultValue: false, description: 'Faire docker login avec harbor-credentials')
        booleanParam(name: 'DEPLOY', defaultValue: false, description: 'Lancer docker compose up -d spam-api')
        string(name: 'REMOTE_HOST', defaultValue: '', description: 'Host distant pour le déploiement (SSH)')
        string(name: 'REMOTE_USER', defaultValue: '', description: 'Utilisateur SSH sur le host distant')
        string(name: 'REMOTE_DEPLOY_PATH', defaultValue: '/opt/spam-detector', description: 'Dossier contenant docker-compose.prod.yml sur le serveur distant')
        string(name: 'COMPOSE_FILE', defaultValue: 'docker-compose.prod.yml', description: 'Fichier Compose utilise pour le deploiement')
    }

    environment {
        IMAGE_TAG = "${BUILD_NUMBER}"
        IMAGE = "${HARBOR_HOST}/${IMAGE_NAME}:${IMAGE_TAG}"
        IMAGE_LATEST = "${HARBOR_HOST}/${IMAGE_NAME}:latest"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Quality and Tests') {
            steps {
                sh '''
                    docker run --rm --volumes-from jenkins -w "$PWD" python:3.11-slim sh -c "
                        python -m pip install -r requirements.txt &&
                        python -m black --check src tests &&
                        python -m flake8 src tests &&
                        python -m pytest -q
                    "
                '''
            }
        }

        stage('Prepare Dataset') {
            steps {
                sh '''
                    docker run --rm --volumes-from jenkins -w "$PWD" python:3.11-slim sh -c "
                        python -m pip install pandas==2.2.3 &&
                        mkdir -p data &&
                        python - <<'PY'
import os
import urllib.request
import zipfile
import pandas as pd

csv_path = 'data/spam.csv'
if os.path.exists(csv_path):
    print(f'Dataset already exists: {csv_path}')
    raise SystemExit(0)

url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip'
try:
    print('Downloading UCI SMS Spam Collection...')
    urllib.request.urlretrieve(url, '/tmp/smsspamcollection.zip')
    with zipfile.ZipFile('/tmp/smsspamcollection.zip') as archive:
        archive.extract('SMSSpamCollection', '/tmp')
    df = pd.read_csv('/tmp/SMSSpamCollection', sep='\\t', header=None, names=['v1', 'v2'])
except Exception as exc:
    print(f'UCI download failed, using deterministic fallback dataset: {exc}')
    df = pd.DataFrame({
        'v1': ['ham'] * 80 + ['spam'] * 20,
        'v2': [f'Normal meeting message {i}' for i in range(80)]
              + [f'FREE prize win now click {i}' for i in range(20)],
    })

df.to_csv(csv_path, index=False, encoding='latin-1')
print(f'Dataset ready: {csv_path} ({len(df)} rows)')
PY
                    "
                '''
            }
        }

        stage('Train Model') {
            steps {
                sh '''
                    docker run --rm --volumes-from jenkins -w "$PWD" python:3.11-slim sh -c "
                        python -m pip install -r requirements.txt &&
                        python src/train.py
                    "
                '''
                archiveArtifacts artifacts: 'model/spam_model.pkl,model/metrics.json',
                                 fingerprint: true
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -f docker/Dockerfile -t "$IMAGE" -t "$IMAGE_LATEST" .
                '''
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    if command -v trivy >/dev/null 2>&1; then
                        trivy image --severity HIGH,CRITICAL --exit-code 1 "$IMAGE"
                    else
                        echo "Trivy absent dans Jenkins: scan via conteneur aquasec/trivy."
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v trivy-cache:/root/.cache/ \
                            aquasec/trivy:latest image \
                            --severity HIGH,CRITICAL \
                            --exit-code 1 \
                            "$IMAGE"
                    fi
                '''
            }
        }

        stage('Push Harbor') {
            when {
                expression { return params.PUSH_TO_HARBOR }
            }
            steps {
                script {
                    if (params.HARBOR_LOGIN) {
                        withCredentials([
                            usernamePassword(
                                credentialsId: 'harbor-credentials',
                                usernameVariable: 'HARBOR_USER',
                                passwordVariable: 'HARBOR_PASSWORD'
                            )
                        ]) {
                            sh '''
                                echo "$HARBOR_PASSWORD" | docker login "$HARBOR_HOST" \
                                    -u "$HARBOR_USER" --password-stdin
                            '''
                        }
                    }
                    sh '''
                        docker push "$IMAGE"
                        docker push "$IMAGE_LATEST"
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                expression { return params.DEPLOY }
            }
            steps {
                script {
                    if (params.REMOTE_HOST?.trim()) {
                        if (!params.REMOTE_USER?.trim()) {
                            error('REMOTE_USER est obligatoire quand REMOTE_HOST est renseigne.')
                        }
                        sh """
                            ssh ${params.REMOTE_USER}@${params.REMOTE_HOST} '
                                set -eu
                                cd ${params.REMOTE_DEPLOY_PATH}
                                export HARBOR_HOST="${params.HARBOR_HOST}"
                                export IMAGE_TAG="${env.IMAGE_TAG}"
                                docker compose -f ${params.COMPOSE_FILE} pull spam-api || true
                                docker compose -f ${params.COMPOSE_FILE} up -d spam-api
                                docker compose -f ${params.COMPOSE_FILE} ps
                            '
                        """
                    } else {
                        sh """
                            export HARBOR_HOST="${params.HARBOR_HOST}"
                            export IMAGE_TAG="${env.IMAGE_TAG}"
                            docker compose -f ${params.COMPOSE_FILE} up -d spam-api
                            docker compose -f ${params.COMPOSE_FILE} ps
                        """
                    }
                }
            }
        }


    }

    post {
        always {
            sh 'docker image prune -f || true'
        }
    }
}
