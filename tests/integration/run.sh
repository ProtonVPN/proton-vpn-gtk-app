#!/usr/bin/env bash

distribution=$(grep "^ID=" /etc/os-release | awk -F "=" '{print $2}')

if [[ "$CI" == "true" && "$distribution" =~ ^(debian|ubuntu)$ ]]
then
  apt-get update
  apt-get install -y python3-proton-core-internal python3-behave python3-pyotp
elif [[ "$CI" == "true" && "$distribution" == "fedora" ]]
then
  dnf install --refresh -y python3-proton-core-internal python3-behave python3-pyotp
fi

proxychains dbus-run-session -- behave tests/integration/features
