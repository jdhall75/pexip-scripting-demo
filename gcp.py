#!/usr/bin/env python

"""Example of using the Compute Engine API to create and delete instances.

Zips up a Python Bottle application and deploys it to a compute instance

The web app has 2 endpoints

/ - Says a basic hello and give you an uplifting Kanye West quote

/hello/<name>  -    Says a personal hello to whoever places their name in the
                    placeholder position.  This also delivers an uplifting 
                    Kanye West quote

For more information, see the README.md in this repo
"""

import argparse
import os
import time
import zipfile
import googleapiclient.discovery
from google.cloud import storage


def get_all_file_paths(directory):
    """supports create_app_zip to walk the directory for the app file"""

    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths


def create_bucket(bucket_name) -> storage.Bucket:
    """create a storage bucket for transfering the app"""
    storage_client = storage.Client()
    try:
        return storage_client.get_bucket(bucket_name)
    except:
        bucket = storage_client.bucket(bucket_name)
        bucket.storage_class = "STANDARD"
        new_bucket = storage_client.create_bucket(bucket, location="us")

    print(
        "Created bucket successfully {} in location {}".format(
            new_bucket.name, new_bucket.location
        )
    )
    return new_bucket


def create_app_zip(app_dir):
    # path to folder which needs to be zipped

    # calling function to get all file paths in the directory
    file_paths = get_all_file_paths(app_dir)

    # printing the list of all files to be zipped
    print("Following files will be zipped:")
    for file_name in file_paths:
        print(file_name)

    # writing files to a zipfile
    with zipfile.ZipFile("/tmp/app.zip", "w") as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file)

    print("All files zipped successfully!")


def list_instances(compute, project, zone):
    """List compute instances in google project"""
    result = compute.instances().list(project=project, zone=zone).execute()
    return result["items"] if "items" in result else None


def create_instance(compute, project, zone, name, bucket):
    # Get the latest Debian Jessie image.
    image_response = (
        compute.images()
        .getFromFamily(project="debian-cloud", family="debian-10")
        .execute()
    )
    source_disk_image = image_response["selfLink"]

    # Configure the machine
    machine_type = f"zones/{zone}/machineTypes/e2-micro"
    startup_script = open(
        os.path.join(os.path.dirname(__file__), "deps/startup-script.sh"), "r"
    ).read()

    # package and deploy the app to a bucket
    create_app_zip("./app")
    # TODO: make this dynamic
    zip_name = "app.zip"
    file_path = "/tmp/" + zip_name
    app_bucket = create_bucket(bucket)
    blob = app_bucket.blob(os.path.basename("/tmp/app.zip"))

    with open(file_path, "rb") as zf:
        blob.upload_from_file(zf)

    config = {
        "name": name,
        "machineType": machine_type,
        # Specify the boot disk and the image to use as a source.
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": source_disk_image,
                },
            }
        ],
        # Specify a network interface with NAT to access the public
        # internet.
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"name": "External NAT", "networkTier": "PREMIUM"}],
            }
        ],
        # Allow the instance to access cloud storage and logging.
        "serviceAccounts": [
            {
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_write",
                    "https://www.googleapis.com/auth/logging.write",
                ],
            }
        ],
        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        "metadata": {
            "items": [
                {
                    # Startup script is automatically executed by the
                    # instance upon startup.
                    "key": "startup-script",
                    "value": startup_script,
                },
                {"key": "zip", "value": zip_name},
                {"key": "bucket", "value": bucket},
            ]
        },
        "tags": {"items": ["dev-http-server", "http-server"]},
    }

    return compute.instances().insert(project=project, zone=zone, body=config).execute()


def get_instance(compute, project, zone, name):
    return compute.instances().get(project=project, zone=zone, instance=name).execute()


def delete_instance(compute, project, zone, name):
    return (
        compute.instances().delete(project=project, zone=zone, instance=name).execute()
    )


def wait_for_operation(compute, project, zone, operation):
    print("Waiting for operation to finish...")
    while True:
        result = (
            compute.zoneOperations()
            .get(project=project, zone=zone, operation=operation)
            .execute()
        )

        if result["status"] == "DONE":
            print("done.")
            if "error" in result:
                raise Exception(result["error"])
            return result

        time.sleep(1)


def update_firewall(project, compute, ports):
    ports = ports.split(",")
    rule = {
        "kind": "compute#firewall",
        "name": "allow8080",
        "selfLink": f"projects/{project}/global/firewalls/allow8080",
        "network": f"projects/{project}/global/networks/default",
        "direction": "INGRESS",
        "priority": 1000,
        "targetTags": ["dev-http-server"],
        "allowed": [{"IPProtocol": "tcp", "ports": ["8080"]}],
        "sourceRanges": ["0.0.0.0/0"],
    }

    request = compute.firewalls().get(project=project, firewall=rule["name"])
    response = request.execute()
    if not response:
        firewall = compute.firewalls().insert(project=project, body=rule)
        return firewall.execute()

    return response


def main(project, bucket, zone, instance_name, ports, wait=True):
    compute = googleapiclient.discovery.build("compute", "v1")
    update_firewall(project, compute, ports)

    print("Creating instance.")

    operation = create_instance(compute, project, zone, instance_name, bucket)
    wait_for_operation(compute, project, zone, operation["name"])

    instances = list_instances(compute, project, zone)

    print("Instances in project %s and zone %s:" % (project, zone))
    for instance in instances:
        print(" - " + instance["name"])

    instance = get_instance(compute, project, zone, instance_name)

    print(
        """
Instance created.
It will take a minute or two for the instance to complete work.

URL's the instance may be available at are:
"""
    )

    for interface in instance["networkInterfaces"]:
        for ac in interface["accessConfigs"]:
            print("http://{}:8080/".format(ac["natIP"]))

    if wait:
        input()

    print("Deleting instance.")

    operation = delete_instance(compute, project, zone, instance_name)
    wait_for_operation(compute, project, zone, operation["name"])


if __name__ == "__main__":
    """"""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("project_id", help="Your Google Cloud project ID.")
    parser.add_argument("bucket_name", help="Your Google Cloud Storage bucket name.")
    parser.add_argument(
        "--zone", default="us-central1-f", help="Compute Engine zone to deploy to."
    )
    parser.add_argument("--name", default="demo-instance", help="New instance name.")

    parser.add_argument(
        "--ports", default="8080", help="Ports to forward to instance, ie 80,8080"
    )

    args = parser.parse_args()

    main(args.project_id, args.bucket_name, args.zone, args.name, args.ports)
