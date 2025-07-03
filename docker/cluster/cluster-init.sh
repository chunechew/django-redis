PORTS="6380 6381 6382 6383 6384 6385"

for port in $PORTS
do
    echo "Starting Redis server on port ${port}..."
    redis-server /etc/redis/redis.conf --port "${port}" --cluster-config-file "${port}.conf" --dbfilename "dump-${port}.rdb" --appendfilename "aof.${port}.base.rdb" &> /dev/null
done

RETRY_INTERVAL=2
MAX_RETIRES=60

for port in $PORTS
do
    count=0
    while true
    do
        echo "Checking Redis server on port ${port} (count: ${count})..."
        RESPONSE=$(redis-cli -p "${port}" ping)

        if [ "$RESPONSE" = "PONG" ]; then
            echo "Redis server on port ${port} is up and running."
            break
        fi

        count=$((count + 1))
        if [ $count = $MAX_RETRIES ]; then
            echo "Redis server on port ${port} failed to start after $MAX_RETRIES attempts."
            exit 1
        fi

        sleep $RETRY_INTERVAL
    done
done

echo "All Redis servers are up and running."
echo "Initializing Redis Cluster..."
#redis-cli --cluster call 127.0.0.1:6380 flushall
#redis-cli --cluster call 127.0.0.1:6380 cluster reset

echo "yes" | redis-cli --cluster create 127.0.0.1:6380 127.0.0.1:6381 127.0.0.1:6382
echo "yes" | redis-cli --cluster add-node 127.0.0.1:6383 127.0.0.1:6380 --cluster-slave
echo "yes" | redis-cli --cluster add-node 127.0.0.1:6384 127.0.0.1:6381 --cluster-slave
echo "yes" | redis-cli --cluster add-node 127.0.0.1:6385 127.0.0.1:6382 --cluster-slave

echo "Checking Redis Cluster status..."
redis-cli --cluster check 127.0.0.1:6380

echo "Redis Cluster initialization complete."
