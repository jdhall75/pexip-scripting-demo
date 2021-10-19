# Deploy a small python app to GCP Compute

The tool used to deploy the app is `gcp.py`.  I borrowed some example code from GCP to get started.  Then sprinkled
my own changes onto it.  There are a list of things that I would like to add to it below.

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

--ports A comma seperated list of ports to forward to the instance

```


