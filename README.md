# Docker Registry Frontend

This Docker Registry UI implementation was created with the idea in mind to have a simple view on huge Docker Registry with the possiblity to easily see how much storage is consumed by which repository.

# Installation

This Registry UI is built with the help of [Sanic](https://github.com/huge-success/sanic), JQuery and Bootstrap.

In order to install the frontend components, execute: `npm i && gulp` in the static folder.
In order to install the backend components, exec `pip install -r requirements.txt` in the root folder.

You can also package the application in a Docker container, the multi-stage Dockerfile in this repository will perform all the necessary steps. `docker build -t docker-registry .`

# Usage

The Registry UI can be started as follows: `python main.py --registry xxx [--username xxx] [--password xxx]`

# Debug

You may want to test the data agregation without serving a WebUI. For this reason you can start the application as follows: `python main.py --registry xxx --cli=true`
