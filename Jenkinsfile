pipeline {
    agent any

    environment {
        IMAGE_NAME = "python-app"
        CONTAINER_NAME = "python-app"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                echo "Latest Commit:"
                git log -1 --pretty=format:"%h | %an | %s"
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                docker build \
                  -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                test -f /opt/secrets/python-app.env || {
                    echo "ERROR: /opt/secrets/python-app.env not found"
                    exit 1
                }

                docker rm -f ${CONTAINER_NAME} || true

                docker run -d \
                  --name ${CONTAINER_NAME} \
                  --restart unless-stopped \
                  --env-file /opt/secrets/python-app.env \
                  -p 5002:5000 \
                  ${IMAGE_NAME}:${BUILD_NUMBER}

                sleep 5

                docker exec ${CONTAINER_NAME} env | grep DB_HOST || {
                    echo "ERROR: DB_HOST not loaded"
                    exit 1
                }

                docker ps | grep ${CONTAINER_NAME} || {
                    echo "ERROR: Container is not running"
                    exit 1
                }
                '''
            }
        }
    }
}
