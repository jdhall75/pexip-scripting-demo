# Deploy a small python app to GCP Compute

The tool used to deploy the app is `gcp.py`. I borrowed some example code from GCP to get started. This script Zips up the app directory and
uploads it to Cloud Storage. The VM pick it up from cloud storage, using the meta server to get the file name and bucket.

There are a list of things that I would like to add to it below.

## Invocation

```
usage: gcp.py [-h] [--zone ZONE] [--name NAME] [--ports PORTS] project_id bucket_name

Required:
    project_id: The project ID you would like to deploy a compute instance for

    bucket_name: an intermediate bucket to hold the application before deploying to the instance.

-h      Help
--zone  Currently the script just goes with the projects default region. Mine was set to
        us-central1 so the options here for the availability-zone are
            us-central1-a
            us-central1-b
            us-central1-c
            us-central1-f
        default: us-central1-f

--name  The name of the instance
        default: demo-instance

--ports A comma seperated list of ports to forward to the instance
        default: 8080

```

## TODO

- The fluent client is install on the host so I am getting syslogs from the server. I would like to query those logs from Cloud Logs and display them as the server boots up.
- I have used skaffold before for Kubernetes. There are a lot of paralles between launching a container on kubernets and launching a VM on GCP compute. I would like to build an underlay / overlay engine to deploy workloads. Being able to define a base then an override to customize your deployment is very powerful. Skaffold is an amazing tool and I would like to see something like it for workig with VMs in the cloud.
