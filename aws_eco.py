#!/usr/bin/env python

__author__ = "Jagat Jyoti Mishra"
__version__ = "1.0.0"
__email__ = "jagatjyoti0@gmail.com"


import argparse
import boto3
import time
import sys
import smtplib
from datetime import datetime
from botocore.exceptions import ClientError

common_string = "-prod-use1-"

#Timestamp prepend to output
def prepend_timestamp():
    i = datetime.now()
    str(i)
    timestamp = i.strftime('%Y/%m/%d %H:%M:%S')
    return str(timestamp)

#Get all instance IDs for selected filter
def get_instance_id(node, product_name, region):
    ec2client = boto3.client('ec2',region)
    try:
        response = ec2client.describe_instances(
            Filters=[{'Name': 'tag:Name','Values': [product_name + common_string + node]}]
        )
    except ClientError as e:
        print(e)
        sys.exit(1)
    instancelist = []
    for reservation in (response["Reservations"]):
        for instance in reservation["Instances"]:
            instancelist.append(instance["InstanceId"])
    return instancelist

#Start all instances for selected filter
def start_instances(node, product_name,region):
    ec2client = boto3.client('ec2',region)
    try:
        response = ec2client.start_instances(InstanceIds=get_instance_id(node, product_name, region))
    except ClientError as e:
        print(e)
        sys.exit(1)

#Stop all instances for selected filter
def stop_instances(node, product_name, region):
    ec2client = boto3.client('ec2',region)
    try:
        response = ec2client.stop_instances(InstanceIds=get_instance_id(node, product_name, region))
    except ClientError as e:
        print(e)
        sys.exit(1)

#Check whether all instances of selected filter stopped
def check_instance_stopped(node, product_name, region):
    ec2client = boto3.client('ec2',region)
    max_retries = 100
    current_retry = 0
    while True:
        try:
            response = ec2client.describe_instances(
                Filters=[{'Name': 'tag:Name','Values': [product_name + common_string + node]},
                        {'Name': 'instance-state-name', 'Values': ['stopped']}])
        except ClientError as e:
            print(e)
            sys.exit(1)
        instancelist = []
        for reservation in (response["Reservations"]):
            for instance in reservation["Instances"]:
                instancelist.append(instance["InstanceId"])
        if len(instancelist) == len(get_instance_id(node, product_name, region)):
            print("[" + prepend_timestamp() + "]" + "[INFO]: All target nodes stopped")
            print("=============================================")
            break
        else:
            time.sleep(6)
            time_elapsed = current_retry * 10
            print("[" + prepend_timestamp() + "]" + "[INFO]: Some nodes still stopping. Seconds elapsed: ", time_elapsed)
        current_retry += 1
        if current_retry > max_retries:
            print("[" + prepend_timestamp() + "]" + "[ERROR]: Timed out waiting for instance to stop")

#Check whether all instances of selected filter started
def check_instance_started(node, product_name, region):
    ec2client = boto3.client('ec2',region)
    max_retries = 100
    current_retry = 0
    while True:
        try:
            response = ec2client.describe_instances(
                Filters=[{'Name': 'tag:Name','Values': [product_name + common_string + node]},
                        {'Name': 'instance-state-name', 'Values': ['running']}])
        except ClientError as e:
            print(e)
            sys.exit(1)
        instancelist = []
        for reservation in (response["Reservations"]):
            for instance in reservation["Instances"]:
                instancelist.append(instance["InstanceId"])
        if len(instancelist) == len(get_instance_id(node, product_name, region)):
            print("[" + prepend_timestamp() + "]" + "[INFO]: All target nodes started")
            print("=============================================")
            break
        else:
            time.sleep(6)
            time_elapsed = current_retry * 10
            print("[" + prepend_timestamp() + "]" + "[INFO]: Some nodes still starting. Seconds elapsed: ", time_elapsed)
        current_retry += 1
        if current_retry > max_retries:
            print("[" + prepend_timestamp() + "]" + "[ERROR]: Timed out waiting for instance to start")

#Get RDS ID
def get_rds_id(product_name, region):
    Tag = 'Name'
    Key = product_name + common_string + "rds-mysql"
    client = boto3.client('rds', region)
    try:
        response = client.describe_db_instances()
    except ClientError as e:
        print(e)
        sys.exit(1)
    for resp in response['DBInstances']:
        db_instance_arn = resp['DBInstanceArn']
        try:
            response = client.list_tags_for_resource(ResourceName=db_instance_arn)
        except ClientError as e:
            print(e)
            sys.exit(1)
        for tags in response['TagList']:
                if tags['Key'] == str(Tag) and tags['Value'] == str(Key):
                        status = resp['DBInstanceStatus']
                        InstanceID = resp['DBInstanceIdentifier']
                        return InstanceID

#Stop RDS
def stop_rds_instance(product_name, region):
    client = boto3.client('rds', region)
    response = client.stop_db_instance(DBInstanceIdentifier=get_rds_id(product_name, region))
    max_retries = 100
    current_retry = 0
    while True:
        try:
            response = client.describe_db_instances(
                DBInstanceIdentifier=get_rds_id(product_name, region)
            )
        except ClientError as e:
            print(e)
            sys.exit(1)
        rds_state = (response['DBInstances'][0]['DBInstanceStatus'])
        if rds_state == "stopped":
            print("[" + prepend_timestamp() + "]" + "[INFO]: RDS instance stopped")
            break
        else:
            time.sleep(10)
            time_elapsed = current_retry * 10
            print("[" + prepend_timestamp() + "]" + "[INFO]: Stopping RDS. Seconds elapsed: ", time_elapsed)
        current_retry += 1
        if current_retry > max_retries:
            print("[" + prepend_timestamp() + "]" + "[ERROR]: Timed out waiting for RDS to stop")

#Start RDS
def start_rds_instance(product_name, region):
    client = boto3.client('rds', region)
    try:
        response = client.start_db_instance(DBInstanceIdentifier=get_rds_id(product_name, region))
    except ClientError as e:
        print(e)
        sys.exit(1)
    max_retries = 180
    current_retry = 0
    while True:
        try:
            response = client.describe_db_instances(
                DBInstanceIdentifier=get_rds_id(product_name, region)
            )
        except ClientError as e:
            print(e)
            sys.exit(1)
        rds_state = (response['DBInstances'][0]['DBInstanceStatus'])
        if rds_state == "available":
            print("[" + prepend_timestamp() + "]" + "[INFO]: RDS instance running")
            break
        else:
            time.sleep(10)
            time_elapsed = current_retry * 10
            print("[" + prepend_timestamp() + "]" + "[INFO]: Starting RDS. Seconds elapsed: ", time_elapsed)
        current_retry += 1
        if current_retry > max_retries:
            print("[" + prepend_timestamp() + "]" + "[ERROR]: Timed out waiting for RDS to start")

#Get ASG Name
def get_asg_name(product_name, region):
    client = boto3.client('autoscaling', region)
    try:
        response = client.describe_auto_scaling_groups()
    except ClientError as e:
        print(e)
        sys.exit(1)
    all_asg = response['AutoScalingGroups']
    for x in all_asg:
        for y in x['Tags']:
            if y['Key'].lower() == 'project' and y['Value'].lower() == product_name + '-share':
                return x['AutoScalingGroupName']

#Decrease node count for ASG so that specified instances are terminated
def decrease_asg_count(product_name, region):
    client = boto3.client('autoscaling', region)
    try:
        response = client.update_auto_scaling_group(
            AutoScalingGroupName=str(get_asg_name(product_name, region)),
            MinSize=0,
            DesiredCapacity=0,
        )
    except ClientError as e:
        print(e)
        sys.exit(1)

#Increase node count to desired value in ASG
def increase_asg_count(product_name, region):
    client = boto3.client('autoscaling', region)
    try:
        response = client.update_auto_scaling_group(
            AutoScalingGroupName=str(get_asg_name(product_name, region)),
            MinSize=6,
            DesiredCapacity=6,
        )
    except ClientError as e:
        print(e)
        sys.exit(1)

#Check whether all instances in the ASG are running
def check_asg_instances_running(product_name, region):
    client = boto3.client('autoscaling', region)
    try:
        response = client.describe_auto_scaling_instances(MaxRecords=2)
    except ClientError as e:
        print(e)
        sys.exit(1)
    for i in response['AutoScalingInstances']:
        if i['AutoScalingGroupName'] == get_asg_name(product_name, region):
            yield i['InstanceId']

#Parser function for handling command line arguments
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('control_environment', type=str, help='function to call control_environment')
    parser.add_argument('operation', type=str, help='start/stop the environment')
    parser.add_argument('product_name', type=str, help='product name, values can be jjm or spg or sbx')
    parser.add_argument('region', type=str, help='region, shorthand like us-east-1')

    args = parser.parse_args()

    eval(args.control_environment)(args.operation, args.product_name, args.region)

#Main function responsible for bringing up or shutting down the environment
def control_environment(operation, product_name, region):
    available_product = ['k8s']
    if product_name not in available_product:
        print("[FATAL]: Error matching product name with available products. Accepted inputs: k8s. Aborting ...")
        sys.exit(2)
    if operation == "start":
        print("")
        print("[MESSAGE]: Initiating START sequence on product " + product_name + " in region " + region + " . Press CTRL + C if not intended. Wait time is 5 seconds")
        print("")
        time.sleep(5)
        #start sequence
        get_rds_id(product_name, region)
        print("=============================================")
        print("[" + prepend_timestamp() + "]" + "[INFO]: Starting associated RDS instance ...")
        start_rds_instance(product_name, region)
        node_list = ['bastion*', 'ca*', 'master', 'etcd*']
        for node in node_list:
                print("=============================================")
                print("[" + prepend_timestamp() + "]" + "[INFO]: Getting instances for " + node)
                get_instance_id(node, product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Starting all instances for " + node)
                start_instances(node, product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Checking state for all instances of " + node)
                check_instance_started(node, product_name, region)
        print("[" + prepend_timestamp() + "]" + "[INFO]: Scaling up instances in ASG")
        increase_asg_count(product_name, region)
        print("[" + prepend_timestamp() + "]" + "[INFO]: Instances should be getting created in ASG ...")
        time.sleep(150)
        subj = "Subject: [ AWS K8s ] status: success | environment : " + product_name + " | state : " + operation + "ed\n"
        text = "Please note " + product_name + " environment has been brought up successfully.\nAll resources are accessible now.\n\nRegards,\naws_eco"
        mail_notification(product_name, text, subj)
        print("[" + prepend_timestamp() + "]" + "[INFO]: ****  Environment brought up successfully  ****")
    elif operation == "stop":
        #stop sequence
        print("")
        print("[MESSAGE]: Initiating STOP sequence on product " + product_name + " in region " + region + " . Press CTRL + C if not intended. Wait time is 5 seconds")
        print("")
        time.sleep(5)
        node_list = ['node', 'etcd*', 'master', 'ca*', 'bastion*']
        for node in node_list:
            if node == "node":
                print("=============================================")
                print("[" + prepend_timestamp() + "]" + "[INFO]: Getting instances for " + node)
                get_instance_id(node, product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Modifying ASG node count for " + node)
                decrease_asg_count(product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Allowing node instances to get terminated ...")
                time.sleep(150)
            else:
                print("=============================================")
                print("[" + prepend_timestamp() + "]" + "[INFO]: Getting instances for " + node)
                get_instance_id(node, product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Stopping all instances for " + node)
                stop_instances(node, product_name, region)
                print("[" + prepend_timestamp() + "]" + "[INFO]: Checking state for all instances of " + node)
                check_instance_stopped(node, product_name, region)
        get_rds_id(product_name, region)
        print("=============================================")
        print("[" + prepend_timestamp() + "]" + "[INFO]: Stopping associated RDS instance ...")
        stop_rds_instance(product_name, region)
        subj = "Subject: [ AWS K8s ] status: success | environment : " + product_name + " | state : " + operation + "ped\n"
        text = "Please note " + product_name + " environment has been shut down successfully.\nIt will be accessible tomorrow Morning.\n\nRegards,\naws_eco"
        mail_notification(product_name, text, subj)
        print("[" + prepend_timestamp() + "]" + "[INFO]: ****  Environment shut down successfully  ****")
    else:
        print("[FATAL]: Invalid operation value supplied. Accepted inputs: start|stop. Aborting ...")
        sys.exit(2)

def mail_notification(product_name, text, subj):
    sender = "jagatjyoti0@gmail.com"
    receivers = ['jagatjyoti0@gmail.com']
    message = subj + text
    try:
       smtpObj = smtplib.SMTP('smtp.gmail.com:25')
       smtpObj.sendmail(sender, receivers, message)
       print("[" + prepend_timestamp() + "]" + "[INFO]: Notifying recipients about status via Mail")
    except smtplib.SMTPException as e:
       print(e)
       print("[" + prepend_timestamp() + "]" + "[ERROR]: Failed sending Mail")

#Main
if __name__ == '__main__':
    main()
