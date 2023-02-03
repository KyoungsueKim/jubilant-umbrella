FROM python:3.11.1

EXPOSE 8000
COPY ./jubilant-umbrella /opt/project/jubilant-umbrella
COPY requirements.txt /opt/project/

RUN pip install --no-cache-dir --upgrade -r /opt/project/requirements.txt
CMD python3 /opt/project/jubilant-umbrella/main.py