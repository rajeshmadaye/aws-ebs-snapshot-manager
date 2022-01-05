#!/usr/bin/python3
#*******************************************************************************
## Application      : snapshotManager
## Description      : Application to list / delete snapshot for current account.
## Author           : Rajesh Madaye
## Copyright        : Copyright 2022, Snapshot Manager
## Version          : 1.0.0
## Mmaintainer      : Rajesh Madaye
## Email            : rajeshmadaye@yahoo.com
## Status           : Developoment Done
##
##*******************************************************************************
## Description
##*******************************************************************************
## 1. Take require inputs from user
## 2. Iterate through all EBS snapshots in ec2 for a provided region
## 3. Produce CSV output with below detail -
##     AccountID,SnapshotId,VolumeId,VolumeSize,InstanceId,AMIID,SnapshotCreationTime
## 4. Delete all snapshots which are older than <older-days> number of days.
## 5. If there is a tag on the EBS volume. (it will be deleted only if correct <tags-data> is given in arguments)
##
# *******************************************************************************
# Version Info:
# 1.0.0 : 05-Jan-2022 : First draft development in completed
#
# *******************************************************************************
import logging
import sys, argparse, re, time, csv
import os.path
from tendo import singleton
from os import path
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from boto3.session import Session
import time
import pytz
import traceback

#*******************************************************************************
# Check if another instance is running
#*******************************************************************************
try:
 me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running
except:
 print("Exception:: Another instance of same script is running")
 sys.exit(2)

##***********************************************************************
## Define global variables
##***********************************************************************
PROFILE         = None        # AWS Profile name
DEF_ACTION      = 'list'      # Default actions will be list all snapshots from given region.
DEF_OLDER_DAYS  = 0           # Default all snapshots will be considered.
DEF_TAGS        = None        # Default tags in key-value pair is none
DEF_CSV_PATH    = '/tmp'      # CSV Creation path
DEF_WAIT_PERIOD = 5           # 05 seconds wait interval in case of attempting to delete thousands of snapshots
DEF_DRY_RUN     = False       # Dry run boolean value, True=It will not delete snapshot, False=It will delete snapshot
empty           = None
yyyymmdd        = datetime.today().strftime('%Y%m%d')
hhmm            = datetime.today().strftime('%H%M')

##***********************************************************************
## Logger Configuration
##***********************************************************************
LOG_FILE_ENABLED  = True
LOG_FILENAME      = '/tmp/SnapshotManager.log' #Provide log file path
LOG_LEVEL         = logging.DEBUG #1. CRITICAL, 2. ERROR, 3. WARN, 4. INFO, 5. DEBUG

##***********************************************************************
## Setup boto3 module
##***********************************************************************
if PROFILE:
  boto3.setup_default_session(profile_name=PROFILE)

##***********************************************************************
## Define class structure
##***********************************************************************
class SnapshotManager:
  def __init__(self, args):
    self.region     = args.region
    self.action     = args.action
    self.olderDays  = args.older_days
    self.tagsData   = args.tags_data
    self.csvpath    = args.csv
    self.logger     = self.getLogger('SnapshotManager')
    self.totalSnapshotCount = 0
    self.totalSnapshotSize  = 0
    
    return

  def run(self):
    rc = False
    self.logger.info('Application execution initiated successfully.')
    if(self.validateInputParams()):
      self.ec2      = boto3.client('ec2', region_name=self.region)
      snapshots     = self.getSnapshots()
      volumes       = self.getVolumes()
      ec2Instances  = self.getEC2Instances()
      self.setSnapshotStruct(snapshots, volumes, ec2Instances)
      if self.action == 'list':
        self.logger.info('List snapshots request initiated')
        self.logger.info('Total [%s] snapshots found with [%s GB] size.', self.totalSnapshotCount, self.totalSnapshotSize)
        self.prepareCSV(snapshots)
      elif(self.action == 'delete'):
        self.logger.info('Delete snapshots request initiated')
        snapshots = self.excludeDetachedSnapshots(snapshots)
        self.logger.info('Total [%s] snapshots found for deletion with [%s GB] size.', self.totalSnapshotCount, self.totalSnapshotSize)
        self.prepareCSV(snapshots)
        self.deleteSnapshots(snapshots)
    self.logger.info('Application execution completed successfully.')
    return rc

  #*******************************************************************************
  # Input validation
  #*******************************************************************************
  def resetSnapshotCount(self):
    self.totalSnapshotCount = 0
    self.totalSnapshotSize = 0
    return

  #*******************************************************************************
  # Input validation
  #*******************************************************************************
  def validateInputParams(self):
    rc = True
    rc = True if (rc and self.isValidRegion()) else False
    rc = True if (rc and self.isValidAction()) else False
    rc = True if (rc and self.isValidTagsData()) else False
    return rc

  #*******************************************************************************
  # Ensure provided inputs is valid
  #*******************************************************************************
  def isValidRegion(self):
    rc = False
    s = Session()
    regions = s.get_available_regions('rds')
    if self.region in regions:
      rc = True
    else:
      self.logger.error('Invalid region value [%s] pass. Please provide valid region to proceed.', self.region)

    return rc

  def isValidAction(self):
    rc = False
    if(self.action == 'list' or self.action == 'delete'):
      rc = True
    else:
      self.logger.error('Invalid action value [%s] pass. Valid values are [list|delete].', self.action)

    return rc

  def isValidTagsData(self):
    rc = True
    if(self.tagsData):
      tags = self.tagsData.split(':')
      if(len(tags) != 2):
        self.logger.error('Invalid tag value [%s] pass. Valid values are "key:value".', self.tagsData)
        rc = False

    return rc

  #*******************************************************************************
  # Get snapshot list
  #*******************************************************************************
  def getSnapshots(self):
    rc = False
    marker = None
    snapshotList = []
    snapshots = {}
    accountID = boto3.client('sts').get_caller_identity().get('Account')
    filters   = self.getSnapshotFilters()
    deltaTime = datetime.now(pytz.utc) - timedelta(days=self.olderDays)
    paginator = self.ec2.get_paginator('describe_snapshots')
    response_iterator = paginator.paginate(Filters=filters, OwnerIds=[accountID])

    for page in response_iterator:
      snapshotList.extend(page['Snapshots'])

    for snapshot in snapshotList:
      if snapshot['StartTime'] < deltaTime:
        self.totalSnapshotCount += 1
        self.totalSnapshotSize += int(snapshot['VolumeSize'])
        sid = snapshot['SnapshotId']
        snapshots[sid] = snapshot

    return snapshots

  def getSnapshotFilters(self):
    filter = []
    if self.tagsData:
      tags = self.tagsData.split(':')
      tagFilter = {  "Name": "tag:{}".format(tags[0]), "Values": [tags[1]] }
      filter.append(tagFilter)
    return filter

  #*******************************************************************************
  # Get volume list
  #*******************************************************************************
  def getVolumes(self):
    rc = False
    volumes = {}
    volumeList = []
    paginator = self.ec2.get_paginator('describe_volumes')
    response_iterator = paginator.paginate()

    for page in response_iterator:
      volumeList.extend(page['Volumes'])

    for v in volumeList:
      id     = v['VolumeId']
      if(len(v['Attachments'])):
        volume = v['Attachments'][0]
        volumes[id] = { 'vid' : id, 'vstate' : volume['State'], 'vinstance' : volume['InstanceId']}
      else:
        volumes[id] = { 'vid' : id, 'vstate' : empty, 'vinstance' : empty}

    return volumes

  #*******************************************************************************
  # Get EC2 instances
  #*******************************************************************************
  def getEC2Instances(self):
    rc = False
    marker = None
    instanceList = []
    instances = {}
    paginator = self.ec2.get_paginator('describe_instances')
    response_iterator = paginator.paginate()

    for page in response_iterator:
      instanceList.extend(page['Reservations'])

    for inst in instanceList:
      instance = inst['Instances'][0]
      id = instance['InstanceId']
      instances[id] = { 'id' : id, 'type' : instance['InstanceType'], 'ami' : instance['ImageId'] }

    return instances

  #*******************************************************************************
  # Prepare snapshot data structure
  #*******************************************************************************
  def setSnapshotStruct(self, snapshots, volumes, ec2Instances):
    volumeStruct    = { 'vid' : empty, 'vstate' : empty, 'vinstance' : empty }
    instanceStruct  = { 'id' : empty, 'type' : empty, 'ami' : empty }

    for snap in snapshots:
      snapshot = snapshots[snap]
      volumeID = snapshot['VolumeId']
      snapshot['VolumeId'] = volumes[volumeID] if(volumeID and volumeID in volumes) else volumeStruct
      instanceId = snapshot['VolumeId']['vinstance']
      snapshot['InstanceId'] = ec2Instances[instanceId] if(instanceId and instanceId in ec2Instances) else instanceStruct

    return snapshots

  #*******************************************************************************
  # Prepare CSV
  #*******************************************************************************
  def prepareCSV(self, snapshots):
    # check if actual file or directory name is provided
    csvFile = self.get_csvpath()


    #First time write header line
    if(not os.path.exists(csvFile)):
      with open(csvFile, 'w') as csvFh:
        writer = csv.writer(csvFh)
        row = ['AccountID', 'SnapshotId', 'VolumeId', 'VolumeSize', 'InstanceId', 'AMIID', 'SnapshotCreationTime']
        writer.writerow(row)
      csvFh.close()

    #Always append to write data
    with open(csvFile, 'a') as csvFh:
      writer = csv.writer(csvFh)
      for snap in snapshots:
        snapshot = snapshots[snap]
        row = []
        row.append(snapshot['OwnerId'])
        row.append(snapshot['SnapshotId'])
        row.append(snapshot['VolumeId']['vid'])
        row.append(snapshot['VolumeSize'])
        row.append(snapshot['InstanceId']['id'])
        row.append(snapshot['InstanceId']['ami'])
        row.append(snapshot['StartTime'].strftime("%Y-%m-%d %H:%M:%S"))
        writer.writerow(row)
      csvFh.close()

    self.logger.info('csv file [%s] created successfully for [%s] request.', csvFile, self.action)
    return csvFile

  def get_csvpath(self):
    csvpath = self.csvpath
    if os.path.isdir(csvpath):
      csvFile = '{}/aws_snapshots_{}_{}.csv'.format(csvpath, yyyymmdd, hhmm)
    elif os.path.isfile(path):
      csvFile = csvpath
    return csvFile

  #*******************************************************************************
  # Exclude detached snapshots
  #*******************************************************************************
  def excludeDetachedSnapshots(self, snapshots):
    self.resetSnapshotCount()
    excludedSnapshots = {}
    for snap in snapshots:
      snapshot = snapshots[snap]
      if('InstanceId' in snapshot):
        if('ami' in snapshot['InstanceId']):
          if(not snapshot['InstanceId']['ami']):
            excludedSnapshots[snap] = snapshot
            self.totalSnapshotCount = self.totalSnapshotCount + 1
            self.logger.debug('Snapshot [%s] having size [%s GB] will be marked for deletion.', snapshot['SnapshotId'], snapshot['VolumeSize'])
            if snapshot['VolumeSize']:
              self.totalSnapshotSize  = self.totalSnapshotSize + int(snapshot['VolumeSize'])

    return excludedSnapshots

  #*******************************************************************************
  # Delete snapshots
  #*******************************************************************************
  def deleteSnapshots(self, snapshots):
    rc = True
    deleteCount = 0
    for snap in snapshots:
      deleteCount = deleteCount + 1
      snapshot = snapshots[snap]
      try:
        self.ec2.delete_snapshot(
          SnapshotId=snapshot["SnapshotId"],
          DryRun= DEF_DRY_RUN
        )
        self.logger.info('Snapshot [%s] having size [%s GB] deleted successfully', snapshot["SnapshotId"], snapshot['VolumeSize'])
        self.waitProcess(deleteCount)
      except ClientError as e:
        rc = False
        if e.response['Error']['Code'] == 'DryRunOperation':
          self.logger.info('You have permissions to delete snapshot [%s] having size [%s GB]', snapshot["SnapshotId"], snapshot['VolumeSize'])
        else:
          self.logger.error("Delete snapshot operation, unexpected error: %s", e)
    return rc

  def waitProcess(self, deleteCount):
    rc = True
    if deleteCount % 50 == 0:
      self.logger.info('Application has deleted [%s] snapshots. It will wait for [%s] seconds before deleting further snapshots.', deleteCount, DEF_WAIT_PERIOD)
      time.sleep(DEF_WAIT_PERIOD)
    return rc

  #*******************************************************************************
  # Configure logger
  #*******************************************************************************
  def getLogger(self, appName):
    # create logger
    logger = logging.getLogger(appName)
    logger.setLevel(LOG_LEVEL)

    # create formatter
    formatter = logging.Formatter('%(name)s: %(asctime)s: %(levelname)s: %(message)s', '%Y%m%d_%H%M%S')

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # create console handler and set level to debug if logging in file is enabled.
    if LOG_FILE_ENABLED:
      if LOG_FILENAME:
        fh = logging.FileHandler(LOG_FILENAME)
        fh.setLevel(LOG_LEVEL)    #we can set log level differrent for log file
        fh.setFormatter(formatter)
        logger.addHandler(fh)
      else:
        logger.error('Log into file is enabled but log file name is missing')

    return logger

#*******************************************************************************
# Main function
#*******************************************************************************
def main():
  rc = False
  parser = argparse.ArgumentParser(description='EBS Snapshots Management Process.' \
                                  ,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser._action_groups.pop()
  required = parser.add_argument_group('Required arguments')
  optional = parser.add_argument_group('Optional arguments')
  required.add_argument('-r', '--region', type=str, help='AWS region name', required=True)
  optional.add_argument('-a', '--action', type=str, help='Action to perform [list|delete]', default=DEF_ACTION)
  optional.add_argument('-d', '--older-days', type=int, help='Snapshots with older days', default=DEF_OLDER_DAYS)
  optional.add_argument('-t', '--tags-data', type=str, help='Snapshots with tag keys. (Example: "key:value")', default=DEF_TAGS)
  optional.add_argument('-c', '--csv', type=str, help='CSV file path', default=DEF_CSV_PATH)
  args = parser.parse_args()
  if(args.region):
    try:
      SM = SnapshotManager(args)
      SM.run()
      rc = True
    except Exception as e:
      print("Exception :")
      traceback.print_exc()


  return rc

#*******************************************************************************
# S T A R T
#*******************************************************************************
if __name__ == "__main__":
   main()
