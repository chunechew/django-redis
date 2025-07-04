apt update && \
 apt install -y socat && \
 socat UNIX-LISTEN:/tmp/redis.sock,fork TCP:127.0.0.1:6379