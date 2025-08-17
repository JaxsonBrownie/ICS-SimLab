FROM python:3.9-slim@sha256:40007fe18a72a2e7166be350d52dab86b9fe18f2de08e6a38e26422fb247e81e

# Update
RUN apt-get update

RUN pip3 install requests
RUN pip3 install streamlit

# Set TERM environment variable
ENV TERM xterm-256color
ENV FLASK_ENV=production
ENV STREAMLIT_LOG_LEVEL=error

# Copy container source code
WORKDIR /src
COPY ./src/ .