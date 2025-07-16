FROM redis:latest

RUN apt update
RUN apt install -y supervisor

COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./redis.conf /etc/redis/redis.conf

RUN mkdir -p /var/log/redis

COPY ./cluster-init.sh /usr/local/bin/cluster-init.sh
RUN chmod +x /usr/local/bin/cluster-init.sh
RUN /usr/local/bin/cluster-init.sh

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
