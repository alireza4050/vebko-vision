FROM node:18-bookworm-slim AS build
COPY web-panel/package*.json .
RUN npm ci
COPY web-panel/* ./
RUN npm run build

# FROM node:18-bookworm-slim
# USER node
# WORKDIR /home/node/app
# COPY --from=build --chown=node:node web-panel/package*.json .
# RUN npm ci --omit=dev
# COPY --from=build --chown=node:node web-panel/dist/* .

FROM python:3.11.5-slim-bookworm
RUN pip3 install pipenv
WORKDIR /app
COPY tracker/Pipfile* ./
RUN pipenv install
COPY --from=build --chown=node:node web-panel/dist ./static
COPY tracker .

CMD [ "pipenv", "run" , "uvicorn", "server:app", "--workers", "4"]


#FROM raspian/stretch
#RUN echo 'Acquire::http::proxy "socks5h://192.168.1.91:1080";' > /etc/apt/apt.conf.d/99proxy
#RUN sed -i 's/archive.raspbian.org/legacy.raspbian.org/' /etc/apt/sources.list
#RUN apt update && apt install -y libprotobuf10 libmosquittopp1 libconfig++9v5
#COPY /usr/local/bin/dwm*
#COPY /etc/dwm1001


#docker run --cap-add ALL -v /lib/modules:/lib/modules -v /sys:/sys --device /dev/ttyAMA0:/dev/ttyAMA0 --device /dev/mem:/dev/mem --privileged --rm -it --name st raspbian/stretch bash
#docker exec st mkdir /etc/dwm1001
#docker cp /etc/dwm1001/dwm1001.config st:/etc/dwm1001/
#docker cp /etc/dwm1001/dwm1001-proxy.config st:/etc/dwm1001/
#docker cp /usr/local/bin/dwm-daemon st:/usr/local/bin/
#docker cp /usr/local/bin/dwm-proxy st:/usr/local/bin
