### curl in shell
```shell
#!/bin/sh

rm -f /data/arena/runmnt/runner/test/*.*

param=`cat param.json | jq -c`

echo "call /api/v1/game/init..."
# init
curl -H 'Content-Type: application/json' http://10.0.254.1:50051/api/v1/game/init -d ${param}

echo -e "\n"

echo "call /api/v1/game/start..."
# start
curl -H 'Content-Type: application/json' http://10.0.254.1:50051/api/v1/game/start -d '{}'
echo -e "\n"
```
