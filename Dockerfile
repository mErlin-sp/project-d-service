FROM python:3

WORKDIR /usr/src/project-d-service

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python", "./service.py" ]