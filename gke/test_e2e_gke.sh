#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "--- GKE End-to-End Test ---"

# 1. Get the External IP
get_external_ip() {
    kubectl get service course-creator -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null
}

echo "Retrieving External IP..."
IP=$(get_external_ip)
COUNT=0
MAX_WAIT=30 # 30 * 10s = 5 minutes

while [[ -z "$IP" && $COUNT -lt $MAX_WAIT ]]; do
    echo -n "."
    sleep 10
    IP=$(get_external_ip)
    COUNT=$((COUNT+1))
done

if [[ -z "$IP" ]]; then
    echo -e "\n${RED}ERROR: External IP still pending or not found.${NC}"
    exit 1
fi

ENDPOINT="http://$IP"
echo -e "\n${GREEN}Found GKE Endpoint: $ENDPOINT${NC}"

# 2. Check Health
echo "Checking /health endpoint..."
HEALTH=$(curl -s "$ENDPOINT/health")
if [[ "$HEALTH" == '{"status":"ok"}' ]]; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed: $HEALTH${NC}"
    exit 1
fi

# 3. Test Full Flow (Course Creation)
TOPIC="The history of the frisbee"
echo "Testing Course Creation for topic: '$TOPIC'..."
echo "This may take 1-3 minutes..."

# Use curl to call the streaming API
# -N: no buffering
# -s: silent
# -X POST
# -d: data
# We'll save the output to a file and then analyze it
OUTPUT_FILE="e2e_output.ndjson"
curl -N -s -X POST "$ENDPOINT/api/chat_stream" \
     -H "Content-Type: application/json" \
     -d "{\"message\": \"Create a comprehensive course on: $TOPIC\", \"user_id\": \"e2e-test-user\"}" \
     --max-time 300 > "$OUTPUT_FILE" &

CURL_PID=$!

# Wait for the process to finish or for a "result" type to appear in the output
# We check every 5 seconds
TIMEOUT=300
ELAPSED=0
SUCCESS=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    if ! kill -0 $CURL_PID 2>/dev/null; then
        # Curl finished
        break
    fi
    
    if grep -q '"type":[[:space:]]*"result"' "$OUTPUT_FILE" 2>/dev/null; then
        echo -e "\n${GREEN}Found 'result' event in stream!${NC}"
        SUCCESS=true
        kill $CURL_PID 2>/dev/null || true
        break
    fi
    
    echo -n "."
    sleep 5
    ELAPSED=$((ELAPSED+5))
done

if [ "$SUCCESS" = false ]; then
    if grep -q '"type":[[:space:]]*"result"' "$OUTPUT_FILE" 2>/dev/null; then
        echo -e "\n${GREEN}Found 'result' event in stream!${NC}"
        SUCCESS=true
    else
        echo -e "\n${RED}FAILED: Timeout or stream ended without 'result' event.${NC}"
        echo "Last 5 lines of output:"
        tail -n 5 "$OUTPUT_FILE"
        exit 1
    fi
fi

# 4. Validate Result Content
echo "Validating result content..."
RESULT_TEXT=$(jq -r 'select(.type=="result") | .text' "$OUTPUT_FILE")

if [ -z "$RESULT_TEXT" ] || [ "$RESULT_TEXT" = "null" ]; then
    echo -e "${RED}FAILED: Result text is empty.${NC}"
    exit 1
fi

# Basic sanity check on the text length
CHAR_COUNT=$(echo -n "$RESULT_TEXT" | wc -c)
echo "Received course content with $CHAR_COUNT characters."

if [ "$CHAR_COUNT" -lt 100 ]; then
    echo -e "${RED}FAILED: Result text is too short ($CHAR_COUNT chars).${NC}"
    exit 1
fi

echo -e "${GREEN}E2E Test Passed Successfully!${NC}"
rm "$OUTPUT_FILE"
