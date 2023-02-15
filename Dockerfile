FROM python:3.11.2

EXPOSE 8000
COPY ./jubilant-umbrella /opt/project/jubilant-umbrella
COPY requirements.txt /opt/project/

RUN pip install --no-cache-dir --upgrade -r /opt/project/requirements.txt
WORKDIR /opt/project/jubilant-umbrella
CMD python3 -X faulthandler main.py