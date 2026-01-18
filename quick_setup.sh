#!/bin/bash
#===============================================================================
# NetMHCpan MCP Quick Setup Script
#===============================================================================
# This script sets up the complete environment for NetMHCpan MCP server.
# MCP server for NetMHCpan-4.2 - MHC Class I binding prediction.
#
# After cloning the repository, run this script to set everything up:
#   cd netmhcpan_mcp
#   bash quick_setup.sh
#
# Once setup is complete, register in Claude Code with the config shown at the end.
#
# Options:
#   --skip-env        Skip conda environment creation
#   --help            Show this help message
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${SCRIPT_DIR}/env"
PYTHON_VERSION="3.10"

# Print banner
echo -e "${BLUE}"
echo "=============================================="
echo "     NetMHCpan MCP Quick Setup Script        "
echo "=============================================="
echo -e "${NC}"

# Helper functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for conda/mamba
check_conda() {
    if command -v mamba &> /dev/null; then
        CONDA_CMD="mamba"
        info "Using mamba (faster package resolution)"
    elif command -v conda &> /dev/null; then
        CONDA_CMD="conda"
        info "Using conda"
    else
        error "Neither conda nor mamba found. Please install Miniconda or Mambaforge first."
        exit 1
    fi
}

# Parse arguments
SKIP_ENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-env) SKIP_ENV=true; shift ;;
        -h|--help)
            echo "Usage: ./quick_setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-env        Skip conda environment creation"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *) warn "Unknown option: $1"; shift ;;
    esac
done

# Check prerequisites
info "Checking prerequisites..."
check_conda
success "Prerequisites check passed"

# Step 1: Create conda environment
echo ""
echo -e "${BLUE}Step 1: Setting up conda environment${NC}"

if [ "$SKIP_ENV" = true ]; then
    info "Skipping environment creation (--skip-env)"
elif [ -d "$ENV_DIR" ] && [ -f "$ENV_DIR/bin/python" ]; then
    info "Environment already exists at: $ENV_DIR"
else
    info "Creating conda environment with Python ${PYTHON_VERSION}..."
    $CONDA_CMD create -p "$ENV_DIR" python=${PYTHON_VERSION} -y
fi

# Step 2: Install dependencies
echo ""
echo -e "${BLUE}Step 2: Installing dependencies${NC}"

if [ "$SKIP_ENV" = true ]; then
    info "Skipping dependency installation (--skip-env)"
else
    info "Installing core dependencies..."
    "${ENV_DIR}/bin/pip" install fastmcp==2.14.1 loguru==0.7.3 pandas==2.3.3 numpy==2.4.0 tqdm==4.67.1 click==8.3.1

    info "Installing MCP dependencies..."
    "${ENV_DIR}/bin/pip" install --ignore-installed mcp pydantic uvicorn websockets rich
    success "Dependencies installed"
fi

# Step 3: Verify installation
echo ""
echo -e "${BLUE}Step 3: Verifying installation${NC}"

"${ENV_DIR}/bin/python" -c "import fastmcp; import loguru; print('Core packages OK')" && success "Core packages verified" || error "Package verification failed"

# Print summary
echo ""
echo -e "${GREEN}=============================================="
echo "           Setup Complete!"
echo "==============================================${NC}"
echo ""
echo "Environment: $ENV_DIR"
echo ""
echo -e "${YELLOW}Note:${NC} NetMHCpan-4.2 must be installed separately from DTU."
echo "Visit: https://services.healthtech.dtu.dk/services/NetMHCpan-4.2/"
echo ""
echo -e "${YELLOW}Claude Code Configuration:${NC}"
echo ""
cat << EOF
{
  "mcpServers": {
    "netmhcpan": {
      "command": "${ENV_DIR}/bin/python",
      "args": ["${SCRIPT_DIR}/src/server.py"]
    }
  }
}
EOF
echo ""
echo "To add to Claude Code:"
echo "  claude mcp add netmhcpan -- ${ENV_DIR}/bin/python ${SCRIPT_DIR}/src/server.py"
echo ""
