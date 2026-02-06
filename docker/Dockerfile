FROM python:3.13

ARG SOURCE_PATH

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN echo "SOURCE_PATH is $SOURCE_PATH"
COPY $SOURCE_PATH /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]