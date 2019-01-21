FROM node:8-alpine as frontend-builder

RUN mkdir -p /app
WORKDIR /app

RUN npm install -g gulp

ADD static .

RUN npm install && gulp


FROM python:3-alpine

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt

#This is a really dirty hack as it seems to DynamicMessage ProgressBar Widget only supports numbers
RUN sed -i 's/:6.3g//g' /usr/local/lib/python3.7/site-packages/progressbar/widgets.py

COPY --from=frontend-builder /app/vendor .
ADD registryclient.py helper.py main.py ./

CMD ["python", "main.py"]