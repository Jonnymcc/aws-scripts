#! /usr/local/bin/python
import boto3
import argparse
import json


def indent(t, *args):
    print '\t' * t + ' '.join([str(s) for s in args])


def get_instance_name(instance):
    for t in instance['Tags']:
        if t['Key'] == 'Name':
            return t['Value']
    return 'Has no name tag'


def get_instance_block_device(instance, device_name):
    for device in i['BlockDeviceMappings']:
        if device['DeviceName'] == device_name:
            device = {
                'name': device['DeviceName'],
                'delete_on_termination': device['Ebs']['DeleteOnTermination'],
                'id': device['Ebs']['VolumeId']
            }
            return device


parser = argparse.ArgumentParser(
    description='Set EBS block device delete_on_termination attribute on multiple '
    'instances chosen by instance tags.')
parser.add_argument('--device', type=str, required=False, help='/dev/xvdb')
parser.add_argument('--instance-tags', type=json.loads, help='{"env":["production"], ...}')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--region', type=str)
commands = parser.add_mutually_exclusive_group(required=True)
commands.add_argument('--enable', action='store_true')
commands.add_argument('--disable', action='store_true')
args = parser.parse_args()


ec2 = boto3.client('ec2', region_name=args.region)
print 'connected to region', ec2._client_config.region_name

instances = [
    i["Instances"][0] for i in ec2.describe_instances(
        Filters=[{'Name': 'tag:' + k, 'Values': v}
            for k, v in args.instance_tags.items()]
    )['Reservations']
]

for i in instances:
    d = get_instance_block_device(i, args.device)
    if not d:
        continue
    print get_instance_name(i)
    indent(1, d['id'], 'Old setting:', d['delete_on_termination'])

    if not args.dry_run:
        ec2.modify_instance_attribute(
            InstanceId=i['InstanceId'],
            BlockDeviceMappings=[
                {
                    'DeviceName': args.device,
                    'Ebs': {'DeleteOnTermination': args.enable or not args.disable}
                }
            ]
        )
