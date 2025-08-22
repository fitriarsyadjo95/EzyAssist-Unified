#!/bin/bash

# Campaign System Test Runner
# Comprehensive testing script for the campaign registration system

set -e

echo "🧪 Campaign System Test Runner"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_URL="https://ezyassist-unified-production.up.railway.app"
ADMIN_USERNAME="admin@ezymeta.global"
ADMIN_PASSWORD="Password123!"

# Check if URL is provided
if [ "$#" -eq 0 ]; then
    echo -e "${YELLOW}No URL provided. Using default: $DEFAULT_URL${NC}"
    URL="$DEFAULT_URL"
else
    URL="$1"
fi

echo -e "${BLUE}Testing URL: $URL${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if requests library is available
python3 -c "import requests" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing required Python packages...${NC}"
    pip3 install requests
}

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Run the comprehensive test
echo -e "${BLUE}🚀 Starting comprehensive tests...${NC}"
echo ""

python3 comprehensive_test_script.py "$URL" --admin-username "$ADMIN_USERNAME" --admin-password "$ADMIN_PASSWORD"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
    echo -e "${GREEN}   Campaign system is ready for production use.${NC}"
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    echo -e "${RED}   Please review the test results and fix issues before production deployment.${NC}"
fi

echo ""
echo -e "${BLUE}📁 Check the generated test results file for detailed analysis.${NC}"

exit $exit_code