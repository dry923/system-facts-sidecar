# system-facts-sidecar
Python script that waits for a "get" command on a communication IP/Port.
It will then read the input file executing the commands and writing the result to Redis.

# command parameters
| Option | Description | Default |
|--------|-------------|---------|
| --ip | IP to use for command communication | 127.0.0.1 |
| --port | Port to use for command communication | 7777 |
| --redis-port | Redis communication port number | 6379 |
| --redis-ip | Redis IP address | |
| --input-file | Input file path | |
| --log-level | Logging level | INFO |

# input file format
The input file should be in the format key:command
For example:
```
cluster_name:oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}'
sdn:oc get network.config/cluster -o jsonpath='{.status.networkType}'
openshift_version:oc version -o json | jq -r '.openshiftVersion'
platform:oc get infrastructure cluster -o jsonpath='{.status.platformStatus.type}'
```
