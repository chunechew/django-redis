FROM redis:latest

RUN mkdir -p /etc/redis
RUN chmod 777 /etc/redis
COPY sentinel.conf /etc/redis/sentinel.conf

CMD ["redis-server", "/etc/redis/sentinel.conf", "--port", "26379", "--sentinel", "--enable-debug-command", "yes", "--protected-mode", "no"]
