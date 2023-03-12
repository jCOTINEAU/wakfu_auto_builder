docker run \
    --rm \
    --network host \
    -e SONAR_HOST_URL="http://localhost:9001" \
    -e SONAR_LOGIN="sqp_f2ebbf599b9a9afcf3a3915b4dff2b824157e81f" \
    -v "$PWD:/usr/src" \
    sonarsource/sonar-scanner-cli -Dsonar.projectKey="wakfu-auto-builder"
