FROM apache/spark:3.5.3-python3

USER root

WORKDIR /opt/project

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --upgrade "pip<25.1"

RUN pip3 install --no-cache-dir \
    --default-timeout=300 \
    --retries=5 \
    -r /tmp/requirements.txt

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

ENV PYTHONPATH=/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.7-src.zip:/opt/project

RUN mkdir -p /opt/project /root/.ivy2

EXPOSE 8888 4040