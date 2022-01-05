# AWS Snapshot Management application

This project contains source code and supporting files for a AWS Snapshot Management application.

## Package installation steps

User should use below command to install this package.
```bash
root@vps123456:/opt#pip install git+https://github.com/rajeshmadaye/aws-snapshot-mgr
```

## Post Installation Components

Below components will be created by snapshotManager package.
```bash
  /usr/local/bin/snapshotManager.py
  /usr/local/lib/python3.6/dist-packages/snapshotManager-0.1.dist-info/*
```

## Snapshot Manager package usage

Run below command to use snapshotManager package
```bash
root@vps123456:/opt#snapshotManager.py -h
usage: snapshotManager.py [-h] -r REGION [-a ACTION] [-d OLDER_DAYS]
                          [-t TAGS_DATA] [-c CSV]

EBS Snapshots Management Process.

Required arguments:
  -r REGION, --region REGION
                        AWS region name (default: None)

Optional arguments:
  -a ACTION, --action ACTION
                        Action to perform [list|delete] (default: list)
  -d OLDER_DAYS, --older-days OLDER_DAYS
                        Snapshots with older days (default: 0)
  -t TAGS_DATA, --tags-data TAGS_DATA
                        Snapshots with tag keys. (Example: "key:value")
                        (default: None)
  -c CSV, --csv CSV     CSV file path (default: /tmp)

```

## Package uninstallation steps

User should use below command to uninstall snapshotManager package.
```bash
root@vps123456:/opt#pip uninstall snapshotManager
```
