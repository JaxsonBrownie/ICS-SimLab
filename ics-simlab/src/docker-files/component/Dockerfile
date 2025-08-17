FROM ubuntu:20.04@sha256:9ad52fdb4654bb6f0ac2e76e4fb5f12a53c713a656ef0cb1aaa18d3eca378748

# Update
RUN apt-get update

# Install required packages for python
RUN apt-get install -y python3 \
    && apt-get install -y python3-pip 

RUN pip3 install pymodbus
RUN pip3 install pyserial
RUN pip3 install numpy
RUN pip3 install flask

# Set environment variables
ENV TERM xterm-256color
ENV FLASK_ENV=production
ENV STREAMLIT_LOG_LEVEL=error

# Copy container source code
WORKDIR /src
COPY ./src/ .