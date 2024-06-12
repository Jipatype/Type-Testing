#!/bin/sh
now="$(date)"
git add .
git commit -m "$now"
git push