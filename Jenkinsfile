pipeline {
    agent any

    environment {
        PYTHON_IMAGE = 'python:3.12-slim'
        IMAGE_NAME = 'arithmetic-app'
        APP_DIR = 'ArithmeticApp'
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
                    echo '⚙️ Setting up virtual environment and installing dependencies...'
                    sh '''
                        cd ${APP_DIR}
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt bandit safety pytest
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
                    echo '🔍 Running Bandit for security scan...'
                    sh '''
                        cd ${APP_DIR}
                        . venv/bin/activate
                        bandit -r .
                    '''
                }
            }
        }

        stage('Dependency Vulnerability Scan (Safety)') {
            steps {
                script {
                    echo '🔒 Checking dependencies for vulnerabilities...'
                    sh '''
                        cd ${APP_DIR}
                        . venv/bin/activate
                        safety check --full-report
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo '🐳 Building Docker image...'
                    sh '''
                        cd ${APP_DIR}
                        docker-compose build
                    '''
                }
            }
        }

    stage('Container Vulnerability Scan (Trivy)') {
        steps {
            echo '🧯 (Skipping Trivy scan — not installed in Jenkins container)'
        }
    }


        stage('Deploy Application') {
            steps {
                script {
                    echo '🚀 Deploying Flask app using Docker Compose...'
                    sh '''
                        cd ${APP_DIR}
                        docker-compose up -d
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
