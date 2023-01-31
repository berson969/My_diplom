FROM python:3.10

RUN apt update && apt install -y curl

COPY ./requirements.txt /home/
RUN pip3 install --no-cache-dir --upgrade -r /home/requirements.txt

COPY ./backend /home/backend
COPY ./netology_pd_diplom /home/netology_pd_diplom
ADD ./manage.py /home/
ADD ./config.py /home/
ADD ./run.sh /home/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

WORKDIR /home

RUN chmod +x /home/run.sh

ENTRYPOINT ["/home/run.sh"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]