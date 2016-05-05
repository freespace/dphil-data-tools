#!/bin/bash

function pdf2png {
  pdffile="$1"
  pngfile="$(echo "$pdffile" | sed 's/pdf$/png/')"

  echo "Converting $pdffile to png..."

  convert -density 300 "$pdffile" "$pngfile"

  if [ $? -eq 0 ]; then
    echo "Done: $pngfile"
    return 0
  else
    echo 'Conversion failed'
    return 1
  fi
}

while [ $# -gt 0 ]; do
  pdf2png "$1"

  if [ $? -ne 0 ]; then
    exit $?
  fi

  shift
done
