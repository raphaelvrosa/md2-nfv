unify-cloudify-plugin
========================

Cloudify plugin to handle Unify orchestrator blueprints.



## Requirements
```
sudo apt-get install python-dev python-pip
```

## Install Cloudify
Get the file get_cloudify.py from: http://docs.getcloudify.org/3.4.0/installation/from-script/
And install it running
```
python get-cloudify.py --version 3.3.1
```


## Install
```
sudo python setup.py develop
```

## Usage

In folder tests, each folder represent a test corresponding with the yaml configs inside such folders.
Each one of the tests file begin with "test_" name. For example, in folder tests/generic there is test_plugin.py
that runs the configuration defined in blueprint.yaml to generate a Unify Virtualizer xml.

Execute:
```
python unify_cfy/use cases/analytics/test_analytics.py
```

In the line above, the python script is going to execute a test using the file "analytics_1.0.yaml"
defined inside the folder unify_cfy/use cases/analytics/. It is going to create xmls files inside the folder
unify_cfy/use cases/analytics/xmls/ as outputs of the blueprint created by the plugin.
All other use cases can be tested in similar way.



## Tests
In folder tests, each folder represent a test corresponding with the yaml configs inside such folders.
Each one of the tests file begin with "test_" name. For example, in folder tests/generic there is test_plugin.py
that runs the configuration defined in blueprint.yaml to generate a Unify Virtualizer xml.

Execute:
```
python unify_cfy/tests/generic/test_plugin.py
```
