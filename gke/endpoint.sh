#!/bin/bash

# Function to get external IP
get_external_ip() {
    kubectl get service course-creator -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null
}

echo "Waiting for external IP of course-creator service..."
IP=$(get_external_ip)
COUNT=0
MAX_WAIT=60 # wait up to 10 minutes (10s * 60)

while [[ -z "$IP" && $COUNT -lt $MAX_WAIT ]]; do
    echo -n "."
    sleep 10
    IP=$(get_external_ip)
    COUNT=$((COUNT+1))
done

if [[ -z "$IP" ]]; then
    echo -e "\nERROR: External IP still pending after wait. Try again later."
    exit 1
else
    echo -e "\nCourse Creator is available at: http://$IP"
fi
