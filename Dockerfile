# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8.11-slim-buster


WORKDIR /app

COPY . /app
COPY requirements.txt .

RUN pip3 install -r requirements.txt 

EXPOSE 4455



ENV SECRET_KEY=thisissupposedtobeasecret
ENV API_KEY=FD5eYClWwPjaySPSfWK3JuYeU
ENV API_SECRET=oQ0zu63fmAdMZZgOAyalUQuK2PKVT4fdnsStYzeO5XTAoZKD16
ENV ACCESS_TOKEN=1418783442070769664-QLyopesfXnSG1IdPVzClg7Iyg2nKdC
ENV ACCESS_SECRET=CoW1x7LYCu16aGnBs29TmSnl6F6DjOnTT84Pr47qTv9pG



CMD ["flask", "run", "-h", "0.0.0.0", "-p", "4455"]



