FROM umihico/aws-lambda-selenium-python:latest

COPY lambda_function.py jobscrape.py models.py ./
CMD [ "lambda_function.lambda_handler" ]