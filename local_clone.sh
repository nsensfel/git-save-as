#!/bin/bash
mkdir -p $1/$2
cd $1/$2
git init --bare .
echo "New repo url: $1/$2"
