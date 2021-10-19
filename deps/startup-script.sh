## Set environment variables
export HOME=/root

# Use the metadata server to get the configuration specified during
# instance creation. Read more about metadata here:
# https://cloud.google.com/compute/docs/metadata#querying
APP_BUCKET=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket -H "Metadata-Flavor: Google")
ZIP_NAME=$(curl http://metadata/computeMetadata/v1/instance/attributes/zip -H "Metadata-Flavor: Google")


# Install Stackdriver logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh

# Install or update needed software
apt-get update
apt-get install -yq supervisor python3 python3-pip python3-venv unzip

# Account to own server process
useradd -m -d /home/pythonapp pythonapp

# Fetch source code
gsutil cp gs://$APP_BUCKET/$ZIP_NAME /tmp
unzip /tmp/$ZIP_NAME -d /opt

# Python environment setup
python3 -m venv /opt/app/.venv
source /opt/app/.venv/bin/activate

/opt/app/.venv/bin/pip install -r /opt/app/requirements.txt

# Set ownership to newly created account
chown -R pythonapp:pythonapp /opt/app

# Put supervisor configuration in proper place
cp /opt/app/python-app.conf /etc/supervisor/conf.d/python-app.conf

# Start service via supervisorctl
supervisorctl reread
supervisorctl update