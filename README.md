# Docker Registry Frontend

[![Build Status](https://travis-ci.org/3r1co/registry-frontend.svg?branch=master)](https://travis-ci.org/3r1co/registry-frontend)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=3r1co_registry-frontend&metric=alert_status)](https://sonarcloud.io/dashboard?id=3r1co_registry-frontend)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=3r1co_registry-frontend&metric=coverage)](https://sonarcloud.io/dashboard?id=3r1co_registry-frontend)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=3r1co_registry-frontend&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=3r1co_registry-frontend)
[![Known Vulnerabilities](https://snyk.io/test/github/3r1co/registry-frontend/badge.svg)](https://snyk.io/test/github/3r1co/registry-frontend) 

This Docker Registry UI implementation was created with the idea in mind to have a simple view on huge Docker Registry with the possiblity to easily see how much storage is consumed by which repository.
Therefore it is built with a little Python backend that handles the repository processing in order to store the amount of tags and their distinct sizes. We found out that it makes more sense to cache these values, rather than computing them on every request.

# Installation

This Registry UI is built with the help of [Sanic](https://github.com/huge-success/sanic) and React.

In order to install the backend components, execute
 
 ```pip install -r requirements.txt``` 
 
 in the root folder.

In order to install the frontend components, execute: 

```npm start``` 

in the frontend folder.

You can also package the application in a Docker container, the multi-stage Dockerfile in this repository will perform all the necessary steps. 

```docker build -t docker-registry .```

# Usage

The Registry UI can be started as follows: 

`python main.py --registry xxx [--username xxx] [--password xxx] [--cacert ./ca.crt] [--cli]`

or:

`docker run --rm -p 8000 registry-ui --registry xxx [--username xxx] [--password xxx] [--cacert ./ca.crt] [--cli]`

# Roadmap

- Clair integration
- Delete functionality
- RBAC

# Debug

You may want to test the data agregation without serving a WebUI. For this reason you can start the application as follows: `python main.py --registry xxx --cli=true`
