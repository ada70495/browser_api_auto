// ============================================
// browser_api_test —— Jenkins 流水线
//
// 前提：
//   1. 宿主机已启动被测服务：docker compose up -d browser-api（监听 9200）
//   2. Jenkins 容器内有 python3 / pip
//   3. 容器访问宿主机用 host.docker.internal
//   4. 需要插件：JUnit、Allure Jenkins Plugin
// ============================================

pipeline {
    agent any

    environment {
        ENV = 'ci'
        BASE_URL = 'http://host.docker.internal:9200/api/v1'
        PYPI = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    }

    stages {
        stage('1. 拉取代码') {
            steps {
                git url: 'https://github.com/ada70495/browser_api_test.git', branch: 'main'
            }
        }

        stage('2. 等待被测服务就绪') {
            steps {
                sh '''
                    echo "等待被测服务：$BASE_URL/../health"
                    ROOT_URL=$(echo "$BASE_URL" | sed 's#/api/v1##')
                    for i in $(seq 1 30); do
                        if curl -fsS "$ROOT_URL/health" >/dev/null 2>&1; then
                            echo "被测服务已就绪"
                            exit 0
                        fi
                        sleep 2
                    done
                    echo "被测服务未就绪，请先在宿主机执行：docker compose up -d browser-api"
                    exit 1
                '''
            }
        }

        stage('3. 安装依赖') {
            steps {
                sh '''
                    python3 -m pip install -q --break-system-packages -i $PYPI -r requirements.txt
                '''
            }
        }

        stage('4. 执行接口用例') {
            steps {
                sh '''
                    mkdir -p reports
                    python3 -m pytest -p no:cacheprovider \\
                        --junitxml=reports/junit-result.xml \\
                        --cov-report=xml:reports/coverage.xml
                '''
            }
        }
    }

    post {
        always {
            junit testResults: 'reports/junit-result.xml', allowEmptyResults: true
            allure includeProperties: false, jdk: '', results: [[path: 'reports/allure_raw']]
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo '浏览器接口自动化全量回归通过'
        }
        failure {
            echo '存在失败用例，请查看 Allure 报告'
        }
    }
}
