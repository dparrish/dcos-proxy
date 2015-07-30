# dcos-proxy
DCOS Frontend Proxy

This is a reverse load balancer based on Nginx that is designed to run on the public slave nodes of a Mesosphere DCOS cluster.

There is a sample json file for running the balancer, which you can use with:

```
dcos marathon app add frontend-balancer.json
```

The refresh job runs every 10 seconds, looking at all your apps with a `VIRTUAL_HOST` label, and creating a proxy entry
directed to the first port supplied.

```json
{
    "constraints": [["hostname", "UNIQUE"]],
    "container": {
        "type": "DOCKER",
        "docker": {
            "image": "registry"
        }
    },
    "labels": {
        "VIRTUAL_HOST": "registry.your.domain.here"
    },
    "id": "registry",
    "cpus": 1,
    "mem": 256,
    "instances": 2,
    "ports": [5000]
}
```

#### Important Notes:

DCOS provisions by-default with Elastic Load Balancers configured with a `HTTP:80/` health check. The nginx configuration in this proxy service responds with 503 to such requests (as they do not match any vhost record), and will result in all public slaves being reported as `unhealthy`. 

Solutions for this include:
    - Change your Public Slave ELB to a `TCP:80` health check
    - Add a `server` block to the `nginx.conf` for a route such as `/elb-status` which responds with `200 OK`
