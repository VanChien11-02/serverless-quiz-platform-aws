# Serverless Online Quiz Platform

Đồ án môn học Điện toán đám mây.

Hệ thống thi trắc nghiệm trực tuyến được triển khai theo kiến trúc
serverless trên AWS Learner Lab.

## AWS Services

- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- Amazon SQS
- Amazon S3
- Amazon CloudWatch
- Amazon VPC
- AWS IAM LabRole

## Week 1 Progress

### Architecture

![Architecture](architecture/week1-architecture.png)

- [x] Research AWS services
- [x] Design serverless architecture
- [x] Create VPC
- [x] Configure IAM LabRole
- [x] Create S3 report bucket
- [x] Create DynamoDB tables
- [x] Create SQS grading queue
- [x] Create Lambda functions
- [x] Create API Gateway
- [x] Test GET /health
- [x] Test GET /exams/{examId}
- [x] Verify CloudWatch logs

## Week2 Progress

- [x] **Exam Management:** Build APIs to create exams, add questions, and fetch exam details using AWS Lambda and DynamoDB.
- [x] **Start Exam:** Initialize exam sessions, randomize question order, and return exam content to candidates.
- [x] **Time Limit:** Validate exam duration on the backend and reject late submissions.
- [x] **Submit Exam:** Receive answers, store records in the `Submissions` table, and push grading requests to Amazon SQS.
- [x] **Auto Grading:** Process grading asynchronously using a Grading Lambda triggered by SQS.
- [x] **Get Result:** Retrieve correct answers count, total questions, and final scores from DynamoDB.
- [x] **API Testing:** Test endpoints with Postman and monitor execution via AWS CloudWatch Logs.

## Current API

### Health Check

GET /health

### Get Exam

GET /exams

GET /exams/{examId}

### Post Exam and Question 

POST /exams

POST /exams/{id}/questions

### Start and submit exam

POST /exams/{id}/start

POST /submissions/{id}/submit

GET /submissions/{id}/result

## Deployment Environment

AWS Learner Lab  
Region: us-east-1
