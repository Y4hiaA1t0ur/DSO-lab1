pipeline {
    agent any

    environment {
        PYTHON_IMAGE = 'python:3.12-slim'
        IMAGE_NAME = 'arithmetic-app'
        APP_DIR = 'ArithmeticApp'
    }

    triggers {
        pollSCM('H/5 * * * *')  // checks every 5 minutes for new commits
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📦 Checking out source code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo '⚙️ Setting up virtual environment with cached dependencies...'
                    sh '''
                        cd ${APP_DIR}

                        mkdir -p $HOME/.cache/pip

                        if [ ! -d "venv" ]; then
                            python3 -m venv venv
                        fi

                        . venv/bin/activate

                        pip install --upgrade pip

                        pip install --cache-dir $HOME/.cache/pip -r requirements.txt bandit safety pytest
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    echo '🧪 Running tests...'
                    sh '''
                        cd ${APP_DIR}
                        . venv/bin/activate
                        pytest
                    '''
                }
            }
        }

        stage('Static Code Analysis (Bandit)') {
            steps {
                script {
                    echo '🔍 Running Bandit security scan...'
                    sh '''
                        cd ${APP_DIR}
                        . venv/bin/activate
                        REPORT_NAME="bandit-report-build-${BUILD_NUMBER}.json"

                        echo "📊 Running fail-fast Bandit scan (High severity)..."
                        # 🚨 Fail build only if HIGH severity found
                        bandit -r . --configfile bandit.yaml --severity-level high

                        echo "💾 Generating full Bandit report (all severities)..."
                        # 🧾 This one must NOT fail the build
                        bandit -r . --configfile bandit.yaml \
                               --severity-level low \
                               --format json | tee "$REPORT_NAME" || true

                        echo "🧾 Bandit JSON report saved as: $REPORT_NAME"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "${APP_DIR}/bandit-report-build-*.json", allowEmptyArchive: true
                }
                failure {
                    echo '🚨 Bandit found high-severity issues — build failed.'
                }
            }
        }





        stage('Dependency Vulnerability Scan (Safety)') {
            environment {
                SAFETY_API_KEY = credentials('SAFETY_API_KEY')
            }
            steps {
                script {
                    echo '🔒 Running Safety dependency vulnerability scan...'
                    sh '''
                        cd ${APP_DIR}
                        . venv/bin/activate

                        REPORT_NAME="safety-report-build-${BUILD_NUMBER}.json"
                        echo "📄 Generating Safety report: $REPORT_NAME"

                        # Fail build on HIGH or CRITICAL vulnerabilities
                        safety scan -r requirements.txt --json --fail-on-severity high | tee "$REPORT_NAME"

                        echo "🧾 Safety JSON report saved as: $REPORT_NAME"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "${APP_DIR}/safety-report-build-*.json", allowEmptyArchive: true
                }
                failure {
                    echo '🚨 Safety scan detected high-severity dependency vulnerabilities. Build stopped.'
                }
            }
        }


        stage('Build Docker Image') {
            steps {
                script {
                    echo '🐳 Building Docker image...'
                    sh '''
                        cd ${APP_DIR}

                        # Define image name and tags
                        IMAGE_NAME="arithmetic-app"
                        BUILD_TAG="build-${BUILD_NUMBER}"

                        echo "🏷️ Building ${IMAGE_NAME}:${BUILD_TAG} ..."
                        docker build -t ${IMAGE_NAME}:${BUILD_TAG} \
                                     -t ${IMAGE_NAME}:latest \
                                     --label "jenkins_build=${BUILD_NUMBER}" \
                                     --label "build_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
                                     .

                        echo "✅ Image built successfully: ${IMAGE_NAME}:${BUILD_TAG}"
                        docker images ${IMAGE_NAME}
                    '''
                }
            }
        }


        stage('Container Vulnerability Scan (Trivy)') {
            steps {
                script {
                    echo '🧯 Running Trivy vulnerability scan on Docker image...'
                    sh '''
                        IMAGE_NAME="arithmetic-app"
                        BUILD_TAG="build-${BUILD_NUMBER}"
                        FULL_IMAGE="${IMAGE_NAME}:${BUILD_TAG}"
                        REPORT_NAME="trivy-report-build-${BUILD_NUMBER}.json"

                        echo "🔍 Scanning image: ${FULL_IMAGE}"

                        # Create cache dir for faster scans
                        mkdir -p ${WORKSPACE}/.trivy-cache

                        # 1️⃣ Fail-fast scan for High/Critical issues (causes pipeline to fail)
                        echo "🚨 Checking for HIGH/CRITICAL vulnerabilities..."
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v ${WORKSPACE}/.trivy-cache:/root/.cache/ \
                            aquasec/trivy image \
                            --severity HIGH,CRITICAL \
                            --exit-code 1 \
                            --ignore-unfixed \
                            ${FULL_IMAGE}

                        # 2️⃣ Full JSON scan for reporting (will NOT fail the build)
                        echo "🧾 Generating complete Trivy JSON report (all severities)..."
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v ${WORKSPACE}/.trivy-cache:/root/.cache/ \
                            -v ${WORKSPACE}:/workspace \
                            aquasec/trivy image \
                            --scanners vuln,secret \
                            --severity LOW,MEDIUM,HIGH,CRITICAL \
                            --format json \
                            -o /workspace/${REPORT_NAME} \
                            ${FULL_IMAGE} || true

                        echo "✅ Trivy JSON report saved: ${REPORT_NAME}"

                        # 3️⃣ Optional: show a summarized readable report for Jenkins logs
                        echo "📋 Summary of findings:"
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v ${WORKSPACE}/.trivy-cache:/root/.cache/ \
                            aquasec/trivy image \
                            --severity LOW,MEDIUM,HIGH,CRITICAL \
                            --ignore-unfixed \
                            ${FULL_IMAGE} || true
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "trivy-report-build-*.json", allowEmptyArchive: true
                }
                failure {
                    echo '🚨 Trivy found high or critical vulnerabilities — build failed.'
                }
            }
        }



        stage('Deploy Application') {
            steps {
                script {
                    echo '🚀 Deploying Flask app using Docker Compose...'
                    sh '''
                        cd ${APP_DIR}

                        IMAGE_NAME="arithmetic-app"
                        BUILD_TAG="build-${BUILD_NUMBER}"

                        echo "🧩 Deploying image: ${IMAGE_NAME}:${BUILD_TAG}"

                        # Make sure the latest tag also points to this build
                        docker tag ${IMAGE_NAME}:${BUILD_TAG} ${IMAGE_NAME}:latest

                        # Bring down any running containers
                        docker-compose down

                        # Update the image tag dynamically in the compose file
                        sed -i "s|image: ${IMAGE_NAME}:.*|image: ${IMAGE_NAME}:${BUILD_TAG}|g" docker-compose.yml

                        # Start fresh with the new image
                        docker-compose up -d --force-recreate

                        echo "✅ Deployment complete. Running containers:"
                        docker ps --filter "ancestor=${IMAGE_NAME}:${BUILD_TAG}"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo '🧹 Cleaning up workspace...'
            cleanWs()
        }
    }
}
