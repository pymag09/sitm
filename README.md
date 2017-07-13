# [S]cript [i]n [t]he [M]iddle.

**SitM** is a broker between `zabbix-agent` and AWS `CloudWatch`.
Default list of `CloudWatch` metric is very limited. Well known problem that memory usage is a custom metric for every EC2 instance within AWS. Using `SitM` it's easy to put any custom metric to `CloudWatch`.

## Requirements.
* `boto` python lib
* zabbix-agent
* Python 3.x

## Architecture.
![SitM](images/arch.png)

## Configuration
Main `SitM`s config file is `/etc/sitm.conf`
```
[common]
region = eu-west-1
instance-id = i-xxxxxxxxx
socket_timeout = 30
port = 10050
host = localhost

[mem-free]
namespace = MEM
unit = Percent
key = vm.memory.size[pavailable]

[metric-name]
namespace = group
unit = Count
key = something
```

## How it works.
`zabbix-agent` is a place where we can take wide range of [default metrics](https://www.zabbix.com/documentation/3.0/manual/config/items/itemtypes/zabbix_agent), plus any [user defind metrics](https://www.zabbix.com/documentation/3.0/manual/config/items/userparameters?s[]=userparameter).
Example:

```
# /etc/zabbix/zabbix_agentd.conf.d/redis.conf
---------------------------------------------------------
UserParameter=redis.db_size,/opt/redis/bin/redis-cli -r 1 -i 1 DBSIZE | awk '{print $1}'
UserParameter=redis.clients,/opt/redis/bin/redis-cli -r 1 -i 1 INFO | grep "connected_clients" | awk -F  ":" '{print $2}'
UserParameter=redis.req,/opt/redis/bin/redis-cli -r 1 -i 1 INFO | grep "instantaneous_ops_per_sec" | awk -F  ":" '{print $2}'
```
The only thing we have to do is to send request to to `zabbix-agent` and put response to `CloudWatch`.
Each non-`[common]` section of config represents single monitoring metric. Just create crontab file to start monitoring avaliable memory:
 ```
 */5 * * * *     zabbix    sitm.py mem-free
 */5 * * * *     zabbix    sitm.py metric-name
 ...
 ```