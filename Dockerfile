FROM node:alpine as frontend-builder

RUN mkdir -p /app
WORKDIR /app

ADD frontend/package.json .
RUN npm install

ADD frontend .
RUN npm run build

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
    pip3 uninstall --yes pip

RUN adduser -D registry && chown registry /app

USER registry
WORKDIR /app
COPY --from=frontend-builder /app/build ./frontend/build/
ADD registryclient.py main.py ./
ADD helpers ./helpers
ADD api ./api

ENTRYPOINT ["/usr/bin/python3", "main.py"]
