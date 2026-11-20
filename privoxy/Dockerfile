FROM debian:bookworm-slim

RUN echo 'Acquire::ForceIPv4 "true";' \
    > /etc/apt/apt.conf.d/99force-ipv4

RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        privoxy \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i \
    's/^listen-address.*/listen-address  0.0.0.0:8118/' \
    /etc/privoxy/config

EXPOSE 8118

CMD ["privoxy", "--no-daemon", "/etc/privoxy/config"]