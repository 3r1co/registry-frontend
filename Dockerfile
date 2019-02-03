FROM golang:alpine AS builder
RUN apk update && apk add --no-cache git ca-certificates && \
    update-ca-certificates && \
    adduser -D -g '' appuser

COPY main.go .
RUN go get -d -v
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /go/bin/registry-ui

FROM node:alpine as frontend-builder

RUN mkdir -p /app
WORKDIR /app

ADD frontend/package.json .
RUN yarn install

ENV GENERATE_SOURCEMAP=false
ADD frontend .
RUN yarn build

FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /go/bin/registry-ui /registry-ui
COPY --from=frontend-builder /app/build /frontend/build/
USER appuser
ENTRYPOINT ["/registry-ui"]