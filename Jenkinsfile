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

                        echo "📊 Running high-severity Bandit scan (fail on critical issues)..."
                        bandit -r . \
                            --exclude venv,__pycache__,tests,*.json,*.md,*.yml,*.yaml \
                            --skip B108 \
                            --severity-level high

                        echo "💾 Generating full Bandit report (JSON format)..."
                        bandit -r . \
                            --exclude venv,__pycache__,tests,*.json,*.md,*.yml,*.yaml \
                            --skip B108 \
                            --severity-level medium \
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
                    echo '🚨 Bandit found high-severity vulnerabilities. Failing build.'
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

                        echo "🔍 Scanning image: ${FULL_IMAGE}"

                        # Make report name include build number
                        REPORT_NAME="trivy-report-${BUILD_NUMBER}.json"

                        # Create cache dir for faster scans
                        mkdir -p ${WORKSPACE}/.trivy-cache

                        # Run Trivy scan with visible output AND JSON report
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v ${WORKSPACE}/.trivy-cache:/root/.cache/ \
                            -v ${WORKSPACE}:/workspace \
                            aquasec/trivy image \
                            --severity CRITICAL \
                            --exit-code 1 \
                            --format json \
                            -o /workspace/${REPORT_NAME} \
                            ${FULL_IMAGE}

                        echo "🧾 Trivy JSON report saved: ${REPORT_NAME}"

                        # Show human-readable summary for Blue Ocean logs
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v ${WORKSPACE}/.trivy-cache:/root/.cache/ \
                            aquasec/trivy image \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            --ignore-unfixed \
                            ${FULL_IMAGE}
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "trivy-report-*.json", allowEmptyArchive: true
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
