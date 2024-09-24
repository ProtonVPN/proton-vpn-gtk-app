#!/usr/bin/env bash

distribution=$(grep "^ID=" /etc/os-release | awk -F "=" '{print $2}')

# Install required dependencies to run the tests in GitLab
if [[ "$CI" == "true" && "$distribution" =~ ^(debian|ubuntu)$ ]]
then
  apt-get update
  apt-get install -y python3-proton-core-internal python3-behave python3-pyotp python3-proton-vpn-network-manager-openvpn python3-proton-keyring-linux
elif [[ "$CI" == "true" && "$distribution" == "fedora" ]]
then
  dnf install --refresh -y python3-proton-core-internal python3-behave python3-pyotp python3-proton-vpn-network-manager-openvpn python3-proton-keyring-linux
fi

if [[ "$CI" == "true" ]]
then
  # When running the tests in a GitLab pipeline we need to:
  # - Use proxychains so that the tests can reach the API through the proxy.
  # - Use dbus-run-session to start a new dbus session bus, required by gnome-keyring.
  # - Unlock the keyring so that the tests can access it.
  proxychains dbus-run-session -- bash -c "echo "" | gnome-keyring-daemon --unlock; behave tests/integration/features"
else
  behave tests/integration/features
fi
