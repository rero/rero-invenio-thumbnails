#!/usr/bin/env bash

# Usage:
#   env DB=postgresql12 SEARCH=opensearch2 CACHE=redis MQ=rabbitmq ./run-tests.sh
# COLORS for messages
NC='\033[0m'                    # Default color
INFO_COLOR='\033[1;97;44m'      # Bold + white + blue background
SUCCESS_COLOR='\033[1;97;42m'   # Bold + white + green background
ERROR_COLOR='\033[1;97;41m'     # Bold + white + red background

# MESSAGES
msg() {
    echo -e "${1}" 1>&2
}
# Display a colored message
# More info: https://misc.flogisoft.com/bash/tip_colors_and_formatting
# $1: choosen color
# $2: title
# $3: the message

colored_msg() {
    msg "${1}[${2}]: ${3}${NC}"
}

info_msg() {
    colored_msg "${INFO_COLOR}" "INFO" "${1}"
}

error_msg() {
    colored_msg "${ERROR_COLOR}" "ERROR" "${1}"
}

error_msg+exit() {
    error_msg "${1}" && exit 1
}

success_msg() {
    colored_msg "${SUCCESS_COLOR}" "SUCCESS" "${1}"
}

success_msg+exit() {
    colored_msg "${SUCCESS_COLOR}" "SUCCESS" "${1}" && exit 0
}

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup() {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

pip_audit_exceptions=""
add_exceptions() {
    pip_audit_exceptions="$pip_audit_exceptions --ignore-vuln $1"""
}

# pytest 8.4.2   CVE-2025-71176 9.0.3
add_exceptions CVE-2025-71176

info_msg "Check vulnerabilities:"
# pytest 8.4.2   CVE-2025-71176 9.0.3
add_exceptions "CVE-2025-71176"
pip-audit ${pip_audit_exceptions}

info_msg "Test formatting:"
ruff format . --check
info_msg "Test linting:"
ruff check

info_msg "Tests:"
pytest "$@"

exit $?
