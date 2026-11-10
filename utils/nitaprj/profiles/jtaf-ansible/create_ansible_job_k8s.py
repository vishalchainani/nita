#!/usr/bin/python3
import os
import sys

import yaml


if len(sys.argv) < 2:
    print("Must provide job name as the first argument")
    sys.exit(1)

job_name = sys.argv[1]
image_name = (
    sys.argv[2]
    if len(sys.argv) >= 3
    else os.environ.get("NITA_ANSIBLE_IMAGE", "ghcr.io/juniper/nita-ansible:latest")
)
working_dir = os.getcwd()

env_data = {}
if os.path.exists("group_vars/env.yaml"):
    with open("group_vars/env.yaml", "r", encoding="utf-8") as env_file:
        env_data = yaml.safe_load(env_file) or {}
else:
    print("No group_vars/env.yaml supplied; using the image's environment.")

job = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {"name": job_name},
    "spec": {
        "backoffLimit": 0,
        "ttlSecondsAfterFinished": 120,
        "template": {
            "spec": {
                "serviceAccountName": "internal-jenknis-pod",
                "containers": [
                    {
                        "name": "nita-ansible",
                        "image": image_name,
                        "workingDir": working_dir,
                        "command": ["/bin/bash"],
                        "args": [f"{job_name}.sh", os.environ.get("build_dir", "None")],
                        "env": [
                            {"name": name, "value": str(value)}
                            for name, value in (env_data.get("env") or {}).items()
                        ],
                        "volumeMounts": [
                            {"name": "default", "mountPath": "/project/"}
                        ],
                    }
                ],
                "volumes": [
                    {
                        "name": "default",
                        "hostPath": {
                            "type": "DirectoryOrCreate",
                            "path": "/var/nita_project",
                        },
                    }
                ],
                "restartPolicy": "Never",
            }
        },
    },
}

with open(f"{job_name}.yaml", "w", encoding="utf-8") as job_file:
    yaml.safe_dump(job, job_file, sort_keys=False)