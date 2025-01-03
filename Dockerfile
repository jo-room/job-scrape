FROM umihico/aws-lambda-selenium-python:3.12.1

RUN pip install requests==2.32.3
COPY lambda_function.py job_scrape.py models.py ./
CMD [ "lambda_function.lambda_handler" ]