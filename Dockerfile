FROM python:3.7.2-alpine

RUN pip install --upgrade pip

RUN adduser -D worker
USER worker
WORKDIR /home/worker

COPY --chown=worker:worker requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

ENV PATH="/home/worker/.local/bin:${PATH}"

COPY --chown=worker:worker rowcountgettersetter.py .

LABEL maintainer="Rob Gates <robert.gates@du.co>" \
      version="1.0.0"

EXPOSE 5000

ENTRYPOINT ["python"]

CMD ["rowcountgettersetter.py"]