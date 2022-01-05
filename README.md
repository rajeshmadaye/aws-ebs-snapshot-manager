# AWS - EBS Snapshot Management application
This project contains source code and supporting files for a python based AWS Snapshot Management application. 
This application can be used to delete older snapshots from AWS environment to reduce cost.

## Features
- Application allows user to list all EBS snapshots which are 'n' days older in given region.
- Application allows user to delete all EBS snapshots which are 'n' days older in given region.
- Application takes require inputs from user
- Iterate through all EBS snapshots in ec2 for a provided region
- Produce CSV output with below detail -
    AccountID,SnapshotId,VolumeId,VolumeSize,InstanceId,AMIID,SnapshotCreationTime
- Delete all snapshots which are older than <older-days> number of days.
- EBS volume will be deleted only if correct <tags-data> is provided in arguments.


## Tech
Below are list of technologies used.
- [Python] - Python script is written to create AMI snapshot manager application.
- [boto3] - Python boto3 SDK used to interact with AWS services.

Below are list of AWS services used in this project.
- [EC2] - Boto3 client object used to interact with EC2 to get list of snapshots.
- [STS] - Boto3 client object used to interact with AWS Security Token Service (STS)


## Package installation steps

User should use below command to install this package.
```bash
root@vps123456:/opt#pip install git+https://github.com/rajeshmadaye/aws-ebs-snapshot-manager

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

## License
MIT

**Free Software, Keep Learning!**
