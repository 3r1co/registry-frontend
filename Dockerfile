FROM node:8-alpine as frontend-builder

RUN mkdir -p /app
WORKDIR /app

RUN npm install -g gulp

ADD static/package.json .
RUN npm install

ADD static .
RUN gulp

FROM alpine

RUN apk add --no-cache python3 \
                       python3-dev \
                       build-base \
                       git && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install sanic && \
    apk del python3-dev \
            build-base \
            git && \
    rm -r /root/.cache


WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt

#This is a really dirty hack as it seems to DynamicMessage ProgressBar Widget only supports numbers
WORKDIR /usr/lib/python3.6/site-packages/progressbar
RUN sed -i 's/:6.3g//g' widgets.py && \
    pip3 uninstall --yes pip uvloop ujson

WORKDIR /app
COPY --from=frontend-builder /app/vendor ./static/vendor
ADD static/index.html static/favicon.ico ./static/
ADD registryclient.py helper.py main.py ./

ENTRYPOINT ["/usr/bin/python3", "main.py"]