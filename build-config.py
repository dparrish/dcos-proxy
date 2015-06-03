#! /usr/bin/env python

"""Build NGINX config for DCOS automatic load balancing."""

__author__ = 'David Parrish <david@dparrish.com>'

from jinja2 import Template
import json
import requests
import subprocess
import sys
import time
import socket


TEMPLATE="""
server {
        listen 80 default_server;
        server_name _; # This is just an invalid value which will never trigger on a real hostname.
        error_log /proc/self/fd/2;
        access_log /proc/self/fd/1;
        return 503;
}

{% for hostname, vhost in vhosts.items() %}
    upstream {{ hostname }} {
        {% for host in vhost.backends %}
            server {{ host }};
        {% endfor %}
    }

    server {
        listen  80;
        gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;

        server_name {{ hostname }};

        proxy_buffering off;
        error_log /proc/self/fd/2;
        access_log /proc/self/fd/1;

        location / {
            proxy_pass http://{{ hostname }};
            include /etc/nginx/proxy_params;
            # HTTP 1.1 support
            proxy_http_version 1.1;
            proxy_set_header Connection "upgrade";
            proxy_set_header Upgrade $http_upgrade;
        }
    }
{% endfor %}
"""

def main(argv):
    try:
        old_config = None
        while True:
            params = {
                'vhosts': {},
            }

            s = requests.Session()
            apps = json.loads(s.get('http://master.mesos:8080/v2/apps').text)
            for app in apps['apps']:
                try:
                    vhost = app['labels']['VIRTUAL_HOST']
                except KeyError:
                    continue
                tasks = json.loads(s.get('http://master.mesos:8080/v2/apps%s/tasks' % app['id'],
                                         headers={'Accept': 'application/json'}).text)
                backends = []
                for task in tasks['tasks']:
                    try:
                        ip = socket.gethostbyname(task['host'])
                    except socket.gaierror:
                        print "Can't look up host %s" % task['host']
                        continue
                    backends.append('%s:%s' % (ip, task['ports'][0]))
                if backends:
                    params['vhosts'][vhost] = {
                        'backends': backends,
                    }

            template = Template(TEMPLATE)
            new_config = template.render(params)
            if new_config != old_config:
                with file('/etc/nginx/sites-available/default', 'w') as fh:
                    fh.write(new_config)
                test = subprocess.Popen(['/usr/sbin/nginx', '-t'], stderr=subprocess.PIPE)
                output = test.communicate()
                if test.returncode != 0:
                    if old_config:
                        print 'Error generating new NGINX configuration, not reloading'
                        return
                    else:
                        raise RuntimeError('Error generating NGINX configuration')
                subprocess.call(['/usr/sbin/nginx', '-s', 'reload'])
                old_config = new_config
            time.sleep(10)
    except KeyboardInterrupt:
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))

