# The egress proxy: the only process on the agent's network with a route off the machine,
# and the only one holding the provider credential. See egress_proxy.py.
FROM python:3.12-slim

COPY egress_proxy.py /egress_proxy.py

# Unprivileged here too. This container holds the key, so it is the one that matters most.
RUN useradd -m -u 1002 egress   # Debian already ships a "proxy" user
USER egress

EXPOSE 8080
CMD ["python3", "-u", "/egress_proxy.py"]
