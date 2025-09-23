#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📋 BookVerse Core Library Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

cd "$PROJECT_DIR"

if [[ ! -d "venv" && ! -n "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  No virtual environment detected. Consider creating one:${NC}"
    echo -e "${YELLOW}   python -m venv venv && source venv/bin/activate${NC}"
    echo ""
fi

echo -e "${BLUE}📦 Checking dependencies...${NC}"
if [[ ! -f ".deps_installed" || "requirements-dev.txt" -nt ".deps_installed" ]]; then
    echo -e "${YELLOW}📥 Installing development dependencies...${NC}"
    pip install -r requirements-dev.txt
    pip install -e .
    touch .deps_installed
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies up to date${NC}"
fi
echo ""

TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
MARKERS=""

while [[ $
    case $1 in
        --unit)
            TEST_TYPE="unit"
            MARKERS="-m unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            MARKERS="-m integration"
            shift
            ;;
        --auth)
            TEST_TYPE="auth"
            MARKERS="-m auth"
            shift
            ;;
        --config)
            TEST_TYPE="config"
            MARKERS="-m config"
            shift
            ;;
        --api)
            TEST_TYPE="api"
            MARKERS="-m api"
            shift
            ;;
        --demo)
            TEST_TYPE="demo"
            MARKERS="-m demo"
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "BookVerse Core Library Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --auth          Run only authentication tests"
            echo "  --config        Run only configuration tests"
            echo "  --api           Run only API tests"
            echo "  --demo          Run only demo application tests"
            echo "  --no-coverage   Skip coverage reporting"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0
            echo "  $0 --unit
            echo "  $0 --integration -v
            echo "  $0 --auth --no-coverage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

PYTEST_CMD="pytest"

if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=bookverse_core --cov-report=term-missing --cov-report=html:htmlcov"
else
    PYTEST_CMD="$PYTEST_CMD --no-cov"
fi

if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [[ -n "$MARKERS" ]]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

echo -e "${BLUE}🧪 Running $TEST_TYPE tests...${NC}"
echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
echo ""

if eval "$PYTEST_CMD"; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [[ "$COVERAGE" == true ]]; then
        echo ""
        echo -e "${BLUE}📊 Coverage Report Generated${NC}"
        echo -e "${BLUE}HTML Report: file://$PROJECT_DIR/htmlcov/index.html${NC}"
        
        if command -v coverage &> /dev/null; then
            COVERAGE_PERCENT=$(coverage report --format=total 2>/dev/null || echo "unknown")
            if [[ "$COVERAGE_PERCENT" != "unknown" ]]; then
                if (( $(echo "$COVERAGE_PERCENT >= 80" | bc -l) )); then
                    echo -e "${GREEN}📈 Coverage: ${COVERAGE_PERCENT}% (Target: 80%+)${NC}"
                else
                    echo -e "${YELLOW}📈 Coverage: ${COVERAGE_PERCENT}% (Target: 80%+)${NC}"
                fi
            fi
        fi
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Demo library validation complete!${NC}"
    echo -e "${GREEN}   Ready for service migration phase${NC}"
    
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}   Please fix failing tests before proceeding${NC}"
    exit 1
fi
