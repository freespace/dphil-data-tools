#!/usr/bin/env bash

FIJI_DIR=""
while [ $# -gt 0 ]; do
  FIJI_DIR="$1"
  shift
done

IJM_DIR="$(pwd)"

if [ "${FIJI_DIR}x" == "x" ]; then
  echo "Please specify path to Fiji.app"
  exit 1
fi

pushd "${FIJI_DIR}"

if [ ! -d 'macros' ]; then
  echo "macros dir not found"
  exit 1
fi

pushd macros

IJMS=$(ls "$IJM_DIR"/*.ijm "$IJM_DIR"/Library.txt)

for IJM in $IJMS; do
  read -p "Install $IJM? [Y/n]" yesno
  case $yesno in
    nN)
      continue
      ;;
  esac
  grep 'Action Tool' $IJM
  if [ $? -eq 0 ]; then
    pushd 'toolsets'
  else
    pushd .
  fi

  ln -s "$IJM" ./

  popd
done

