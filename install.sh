#!/bin/bash

USER_CONFIG_PATH="${HOME}/printer_data/config"
MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
KLIPPER_PATH="${HOME}/klipper"
KLIPPER_VENV_PATH="${HOME}/klippy-env"

DAISY_PATH="${HOME}/daisy"

set -eu
export LC_ALL=C

function preflight_checks {
    if [ "$EUID" -eq 0 ]; then
        echo "[PRE-CHECK] This script must not be run as root!"
        exit -1
    fi

    if ! command -v python3 &> /dev/null; then
        echo "[ERROR] Python 3 is not installed. Please install Python 3 to use Daisy AI!"
        exit -1
    fi

    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F 'klipper.service')" ]; then
        printf "[PRE-CHECK] Klipper service found! Continuing...\n\n"
    else
        echo "[ERROR] Klipper service not found, please install Klipper first!"
        exit -1
    fi

#    install_package_requirements
}

# Function to check if a package is installed
function is_package_installed {
    dpkg -s "$1" &> /dev/null
    return $?
}

function install_package_requirements {
    packages=("" "")
    packages_to_install=""

    for package in "${packages[@]}"; do
        if is_package_installed "$package"; then
            echo "$package is already installed"
        else
            packages_to_install="$packages_to_install $package"
        fi
    done

    if [ -n "$packages_to_install" ]; then
        echo "Installing missing packages: $packages_to_install"
        sudo apt update && sudo apt install -y $packages_to_install
    fi
}

function setup_venv {
    if [ ! -d "${KLIPPER_VENV_PATH}" ]; then
        echo "[ERROR] Klipper's Python virtual environment not found!"
        exit -1
    fi
    declare -x PS1=""
    source "${KLIPPER_VENV_PATH}/bin/activate"
    echo "[SETUP] Installing/Updating dependencies..."
    pip install --upgrade pip
    pip install -r "${DAISY_PATH}/requirements.txt"
    deactivate
    printf "\n"
}


function link_module {
    if [ ! -d "${KLIPPER_PATH}/klippy/extras/daisy" ]; then
        echo "[INSTALL] Linking Daisy AI module to Klipper extras"
        ln -frsn ${DAISY_PATH}/daisy.py ${KLIPPER_PATH}/klippy/extras/daisy
    else
        printf "[INSTALL] Daisy AI Klipper module is already installed. Continuing...\n\n"
    fi
}

function restart_klipper {
    echo "[POST-INSTALL] Restarting Klipper..."
    sudo systemctl restart klipper
}

function restart_moonraker {
    echo "[POST-INSTALL] Restarting Moonraker..."
    sudo systemctl restart moonraker
}


printf "\n=============================================\n"
echo "- Daisy AI install script -"
echo "- Debian and derivatives only. -"
printf "=============================================\n\n"


# Run steps
preflight_checks
setup_venv
link_module
restart_klipper
restart_moonraker