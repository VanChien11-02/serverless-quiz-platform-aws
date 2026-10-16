# AWS Resources - Week 1

Region: us-east-1

## VPC

- VPC: quiz-vpc
- CIDR: 10.0.0.0/16
- Public subnet: 10.0.1.0/24
- Private subnet: 10.0.2.0/24
- Internet Gateway: quiz-vpc-igw
- S3 Gateway Endpoint: quiz-vpc-vpce-s3

## DynamoDB

Tables:
- Users
- Exams
- Questions
- Submissions

## Lambda

- quiz-health-function
- quiz-api-db

## API Gateway

Routes:
- GET /health
- GET /exams
- GET /exams/{examId}

## SQS

- quiz-grading-queue

## S3

- Serverless Quiz report bucket

## CloudWatch

- Lambda logs enabled and verified.

## IAM

- LabRole provided by AWS Learner Lab.