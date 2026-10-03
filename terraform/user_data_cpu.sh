#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting user_data setup for CPU LightGBM benchmark node"

# Setup 1GB swap to guarantee stable memory during pip/ML runs on t3.micro
fallocate -l 1G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=1024
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

apt-get update -y
apt-get install -y python3 python3-pip

pip3 install --upgrade pip
pip3 install lightgbm scikit-learn pandas numpy kaggle

mkdir -p /home/ubuntu/ml-benchmark
chown ubuntu:ubuntu /home/ubuntu/ml-benchmark

echo "CPU environment ready: lightgbm, scikit-learn, pandas, numpy, kaggle installed system-wide."
