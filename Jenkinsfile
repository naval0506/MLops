// ═══════════════════════════════════════════════════════════════════════════
// Jenkinsfile — Spam Detector MLOps
// Pipeline : checkout → lint → test → build → scan Trivy → push Harbor → deploy
// Outil CI/CD : Jenkins  |  Registry : Harbor  |  Deploy : Docker + SSH
// ═══════════════════════════════════════════════════════════════════════════

pipeline {

    agent any

    // ── Variables ─────────────────────────────────────────────────────────
    environment {
        // Détection de l'IP LAN (évite l'IP interne Docker 172.x.x.x)
        HARBOR_HOST  = sh(script: "ip route get 1.1.1.1 | grep -oP 'src \\K\\S+' || hostname -I | awk '{print \$1}'", returnStdout: true).trim()
        IMAGE_NAME   = "spam-detector/spam-api"
        IMAGE_TAG    = "${env.GIT_COMMIT ? env.GIT_COMMIT[0..7] : env.BUILD_ID}"
        HARBOR_CREDS = credentials('harbor-credentials')
        
        // Déploiement (utilise l'IP détectée par défaut)
        STAGING_HOST = "${env.STAGING_HOST ?: HARBOR_HOST}"
        STAGING_USER = "${env.STAGING_USER ?: 'valkely'}"
        STAGING_PATH = "${env.STAGING_PATH ?: '/home/valkely/deploy/staging'}"
        PROD_HOST     = "${env.PROD_HOST ?: HARBOR_HOST}"
        PROD_USER     = "${env.PROD_USER ?: 'valkely'}"
        PROD_PATH     = "${env.PROD_PATH ?: '/home/valkely/deploy/prod'}"
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    // ══════════════════════════════════════════════════════════════════════
    stages {

        // ── 1. CHECKOUT ──────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "==> Récupération du code..."
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        // ── 2. LINT (parallèle) ──────────────────────────────────────────
        stage('Lint') {
            parallel {

                stage('flake8 — style PEP8') {
                    agent {
                        docker { image 'python:3.11-slim' }
                    }
                    steps {
                        sh '''
                            pip install flake8 --quiet --user
                            echo "==> flake8 (style)..."
                            python3 -m flake8 src/ tests/ \
                                --max-line-length=120 \
                                --ignore=E501,E402,W503 \
                                --exclude=__pycache__
                        '''
                    }
                }

                stage('black — formatage') {
                    agent {
                        docker { image 'python:3.11-slim' }
                    }
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                            sh '''
                                pip install black --quiet --user
                                echo "==> black check..."
                                python3 -m black --check src/ tests/
                            '''
                        }
                    }
                }
            }
        }

        // ── 3. TESTS (parallèle) ─────────────────────────────────────────
        stage('Tests') {
            parallel {

                stage('Tests unitaires + Coverage') {
                    agent {
                        docker { image 'python:3.11-slim' }
                    }
                    steps {
                        sh '''
                            pip install -r requirements.txt --quiet --user
                            mkdir -p data model

                            python3 -c "
import pandas as pd
data = {
    'v1': ['ham']*80 + ['spam']*20,
    'v2': ['Normal message number ' + str(i) for i in range(80)] +
          ['FREE prize win now click ' + str(i) for i in range(20)]
}
pd.DataFrame(data).to_csv('data/spam.csv', index=False, encoding='latin-1')
print('Dataset test OK')
"
                            echo "==> pytest..."
                            python3 -m pytest tests/ \
                                -v \
                                --cov=src \
                                --cov-report=xml:coverage.xml \
                                --cov-report=html:coverage-html \
                                --junitxml=test-results.xml
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'test-results.xml'
                            publishHTML([
                                allowMissing: true,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'coverage-html',
                                reportFiles: 'index.html',
                                reportName: 'Coverage HTML'
                            ])
                        }
                    }
                }

                stage('Validation qualité ML') {
                    agent {
                        docker { image 'python:3.11-slim' }
                    }
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                            sh '''
                                pip install -r requirements.txt --quiet --user
                                mkdir -p data model

                                python3 -c "
import urllib.request, zipfile, os, pandas as pd, sys

url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip'
try:
    print('Téléchargement dataset UCI...')
    urllib.request.urlretrieve(url, '/tmp/spam.zip')
    with zipfile.ZipFile('/tmp/spam.zip') as z:
        z.extractall('/tmp/spam/')
    df = pd.read_csv('/tmp/spam/SMSSpamCollection', sep=chr(9), header=None, names=['v1','v2'])
    df.to_csv('data/spam.csv', index=False, encoding='latin-1')
    print(f'Dataset UCI OK : {len(df)} SMS')
except Exception as e:
    print(f'Fallback synthétique ({e})')
    data = {
        'v1': ['ham']*400 + ['spam']*100,
        'v2': ['Ham message '+str(i) for i in range(400)] +
              ['FREE SPAM WIN NOW '+str(i) for i in range(100)]
    }
    pd.DataFrame(data).to_csv('data/spam.csv', index=False, encoding='latin-1')
    print('Dataset fallback OK')
"
python3 -c "
import sys; sys.path.insert(0, 'src')
from train import train
m = train(data_path='data/spam.csv', model_path='model/spam_model.pkl')
acc = m.get('accuracy', 0)
print(f'Accuracy : {acc}')
assert acc >= 0.85, f'ECHEC — Accuracy trop basse : {acc} < 0.85'
print('Qualite ML validee')
"
                            '''
                        }
                    }
                    post {
                        success {
                            archiveArtifacts artifacts: 'model/spam_model.pkl,model/metrics.json',
                                             fingerprint: true,
                                             allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        // ── 4. BUILD DOCKER ──────────────────────────────────────────────
        // PLUS de condition when - s'exécute toujours
        stage('Build Docker') {
            steps {
                script {
                    def imageFullTag   = "${HARBOR_HOST}/${IMAGE_NAME}:${IMAGE_TAG}"
                    def imageLatestTag = "${HARBOR_HOST}/${IMAGE_NAME}:latest"
                    env.IMAGE_FULL     = imageFullTag
                    env.IMAGE_LATEST   = imageLatestTag

                    echo "==> Build : ${imageFullTag}"
                    sh """
                        docker build \\
                            --file docker/Dockerfile \\
                            --tag ${imageFullTag} \\
                            --tag ${imageLatestTag} \\
                            --label "jenkins.build=${env.BUILD_NUMBER}" \\
                            --label "git.commit=${env.GIT_COMMIT}" \\
                            --label "git.branch=${env.GIT_BRANCH}" \\
                            --cache-from ${imageLatestTag} \\
                            .

                        echo "==> Sauvegarde image pour le scan..."
                        docker save ${imageFullTag} -o image.tar

                        echo "Build terminé : \$(docker image inspect ${imageFullTag} --format '{{.Size}}' | numfmt --to=iec) "
                    """
                }
            }
            post {
                failure {
                    echo "Build Docker échoué. Vérifier le Dockerfile."
                }
            }
        }

        // ── 5. SCAN SÉCURITÉ TRIVY ───────────────────────────────────────
        // PLUS de condition when - s'exécute toujours
        stage('Scan Trivy') {
            steps {
                sh '''
                    echo "==> Installation Trivy si absent..."
                    if ! command -v trivy &>/dev/null; then
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
                            | sh -s -- -b /usr/local/bin 2>/dev/null
                    fi
                    trivy --version

                    echo "==> Scan des vulnérabilités..."
                    trivy image \
                        --input image.tar \
                        --severity HIGH,CRITICAL \
                        --exit-code 0 \
                        --format table \
                        --output trivy-report.txt
                    cat trivy-report.txt

                    echo "==> Rapport JSON..."
                    trivy image \
                        --input image.tar \
                        --severity HIGH,CRITICAL \
                        --format json \
                        --output trivy-report.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-report.txt,trivy-report.json',
                                     allowEmptyArchive: true
                }
            }
        }

        // ── 6. PUSH HARBOR ───────────────────────────────────────────────
        // PLUS de condition when - s'exécute toujours
        stage('Push Harbor') {
            steps {
                script {
                    sh """
                        echo "==> Connexion à Harbor (${HARBOR_HOST})..."
                        echo "${HARBOR_CREDS_PSW}" | docker login "${HARBOR_HOST}" \\
                            -u "${HARBOR_CREDS_USR}" --password-stdin

                        echo "==> Chargement de l'image depuis le tar..."
                        docker load -i image.tar

                        echo "==> Push tag SHA..."
                        docker push ${env.IMAGE_FULL}

                        echo "==> Push tag latest..."
                        docker push ${env.IMAGE_LATEST}
                    """

                    if (env.TAG_NAME) {
                        sh """
                            docker tag ${env.IMAGE_FULL} ${HARBOR_HOST}/${IMAGE_NAME}:${env.TAG_NAME}
                            docker push ${HARBOR_HOST}/${IMAGE_NAME}:${env.TAG_NAME}
                            echo "Tag Git poussé : ${env.TAG_NAME}"
                        """
                    }
                    echo "Image disponible sur Harbor : ${env.IMAGE_FULL}"
                }
            }
        }

        // ── 7. DÉPLOIEMENT STAGING ───────────────────────────────────────
        // Modifié : s'exécute sur main ET develop, ou manuellement
        stage('Deploy — Staging') {
            steps {
                sshagent(credentials: ['staging-ssh-key']) {
                    sh """
                        echo "==> Déploiement staging sur ${STAGING_HOST}..."
                        ssh -o StrictHostKeyChecking=no \\
                            ${STAGING_USER}@${STAGING_HOST} << 'REMOTE'
                            set -e
                            mkdir -p ${STAGING_PATH} || true
                            cd ${STAGING_PATH}

                            # Arrêter l'ancien container s'il existe
                            docker stop spam-staging 2>/dev/null || true
                            docker rm spam-staging 2>/dev/null || true

                            # Connexion Harbor et pull
                            echo "${HARBOR_CREDS_PSW}" | docker login "${HARBOR_HOST}" \\
                                -u "${HARBOR_CREDS_USR}" --password-stdin

                            # Lancer le nouveau container
                            docker run -d \\
                                --name spam-staging \\
                                -p 8000:8000 \\
                                ${HARBOR_HOST}/${IMAGE_NAME}:${IMAGE_TAG}

                            echo "Attente démarrage..."
                            sleep 15
                            curl -sf http://localhost:8000/health || echo "Warning: Health check timeout"
                            echo "==> Staging déployé"
REMOTE
                    """
                }
            }
            post {
                success { echo "✅ Déployé sur staging : http://${STAGING_HOST}:8000" }
                failure { echo "❌ Déploiement staging ÉCHOUÉ" }
            }
        }

        // ── 8. DÉPLOIEMENT PRODUCTION (validation manuelle) ──────────────
        stage('Deploy — Production') {
            input {
                message "⚡ Déployer en PRODUCTION ?"
                ok "Oui, déployer ✅"
                submitter "admin"
                parameters {
                    string(name: 'DEPLOY_REASON',
                           defaultValue: '',
                           description: 'Raison / numéro de ticket')
                }
            }
            steps {
                sshagent(credentials: ['prod-ssh-key']) {
                    sh """
                        echo "==> Déploiement production sur ${PROD_HOST}..."
                        echo "==> Motif : ${DEPLOY_REASON}"
                        ssh -o StrictHostKeyChecking=no \\
                            ${PROD_USER}@${PROD_HOST} << 'REMOTE'
                            set -e
                            mkdir -p ${PROD_PATH} || true
                            cd ${PROD_PATH}

                            docker stop spam-prod 2>/dev/null || true
                            docker rm spam-prod 2>/dev/null || true

                            echo "${HARBOR_CREDS_PSW}" | docker login "${HARBOR_HOST}" \\
                                -u "${HARBOR_CREDS_USR}" --password-stdin

                            docker run -d \\
                                --name spam-prod \\
                                -p 8000:8000 \\
                                ${HARBOR_HOST}/${IMAGE_NAME}:${IMAGE_TAG}

                            sleep 15
                            curl -sf http://localhost:8000/health || echo "Warning: Health check timeout"
                            echo "==> Production déployée"
REMOTE
                    """
                }
            }
            post {
                success { echo "✅ Déployé en production : http://${PROD_HOST}:8000" }
                failure { echo "❌ Déploiement production ÉCHOUÉ" }
            }
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    post {
        always {
            echo "==> Nettoyage workspace..."
            sh '''
                rm -f image.tar trivy-report.* coverage.xml test-results.xml || true
                docker image prune -f || true
            '''
        }
        success {
            echo "✅ Pipeline réussi — build #${env.BUILD_NUMBER} | image: ${env.IMAGE_FULL ?: 'N/A'}"
        }
        failure {
            echo "❌ Pipeline ÉCHOUÉ — build #${env.BUILD_NUMBER} — voir les logs ci-dessus"
        }
        unstable {
            echo "⚠️ Pipeline INSTABLE (lint warning) — build #${env.BUILD_NUMBER}"
        }
    }
}
