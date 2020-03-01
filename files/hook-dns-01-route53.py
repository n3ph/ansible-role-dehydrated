#!/usr/bin/env python3

# modules declaration
import os
import sys
import boto3
import tldextract
from time import sleep

# checking environment variables
if 'AWS_PROFILE' not in os.environ:
    raise Exception("Environment variable AWS_PROFILE not defined")

# declaring variables
aws_profile = os.environ['AWS_PROFILE']

# initialize client
session = boto3.Session(profile_name=aws_profile)
client = session.client("route53")

# get hosted_zone_id from domain name
def get_hosted_zone_id(domain):
    global client

    tldextract_nocache = tldextract.TLDExtract(cache_file=False)

    response = client.list_hosted_zones_by_name(
        DNSName=tldextract_nocache(domain).registered_domain,
        MaxItems="1"
    )

    # return sanitized hosted_zone_id
    return response["HostedZones"][0]["Id"].split("/")[-1:][0]

# insert or update challenge record
def upsert_dns_record(domain, txt_challenge):
    global client

    response = client.change_resource_record_sets(
        HostedZoneId=get_hosted_zone_id(domain),
        ChangeBatch={
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': '_acme-challenge.{0}'.format(domain),
                    'Type': 'TXT',
                    'TTL': 60,
                    'ResourceRecords': [{
                        'Value': '"{0}"'.format(txt_challenge)
                    }]
                }
            }]
        }
    )

    # wait 30 seconds for DNS update
    sleep(30)

# delete challenge record
def delete_dns_record(domain, txt_challenge):
    global client

    response = client.change_resource_record_sets(
        HostedZoneId=get_hosted_zone_id(domain),
        ChangeBatch={
            'Changes': [{
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': '_acme-challenge.{0}'.format(domain),
                    'Type': 'TXT',
                    'TTL': 60,
                    'ResourceRecords': [{
                        'Value': '"{0}"'.format(txt_challenge)
                    }]
                }
            }]
        }
    )

# main
if __name__ == "__main__":
    operation = sys.argv[1]

    if operation in ["deploy_challenge", "clean_challenge"]:
        domain = sys.argv[2]
        txt_challenge = sys.argv[4]
    else:
        sys.exit(0)

    if operation == "deploy_challenge":
        upsert_dns_record(domain, txt_challenge)
    elif operation == "clean_challenge":
        delete_dns_record(domain, txt_challenge)
