#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

write_yaml_files.py
python3 ./create_ansible_job_k8s.py build
kubectl create -f build.yaml
pod=""
for attempt in $(seq 1 600); do
    pod=$(kubectl get pods -l job-name=build -o name)
    if [ -n "$pod" ]; then
        break
    fi
    sleep 1
done
if [ -z "$pod" ]; then
    kubectl describe job/build
    echo "Timed out waiting for the Ansible build pod." >&2
    exit 1
fi
kubectl logs "$pod" -f --pod-running-timeout=600s
if ! kubectl wait --for=condition=complete job/build --timeout=30s; then
    kubectl describe job/build
    echo "Ansible build did not complete successfully." >&2
    exit 1
fi
