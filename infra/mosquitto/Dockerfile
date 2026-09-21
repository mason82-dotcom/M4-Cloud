FROM eclipse-mosquitto:2

COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY entrypoint.sh /usr/local/bin/m4-mosquitto-entrypoint

RUN chmod 0755 /usr/local/bin/m4-mosquitto-entrypoint

ENTRYPOINT ["/usr/local/bin/m4-mosquitto-entrypoint"]
