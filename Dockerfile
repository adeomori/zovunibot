FROM python:3.9-bookworm

RUN mkdir /src
COPY . /src
WORKDIR /src

RUN pip3 install -r requierments.txt
CMD ["python3", "bot.py"]
