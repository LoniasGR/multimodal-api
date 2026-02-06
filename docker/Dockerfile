FROM python:3.13

ARG SOURCE_PATH
ARG REQUIREMENTS_FILE

WORKDIR /code

COPY $REQUIREMENTS_FILE /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY $SOURCE_PATH /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]