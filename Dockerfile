FROM python
RUN apt-get update
RUN apt-get install -y python python-pip wget
RUN pip install Flask
RUN pip install Flask-Cors
RUN pip install google-cloud-firestore
RUN pip install requests
RUN pip install pandas
RUN mkdir /app
COPY . /app
WORKDIR app
ENTRYPOINT ["python"]
CMD ["main.py"]
