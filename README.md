# Specification:
## Task: 
### Create a web based file sharing tool with support for sharing with multiple users.
#### How the app works: The user logs into the website and gets a file upload screen. The user chooses the file from local storage and also enters a number of email addresses (upto 5). Once the user hits upload, the file is stored in S3. Also, the link to the file is emailed to the provided email addresses.
#### A list of files uploaded by the user should be stored in a cloud database, for billing purposes.
# Deliverables (i.e, things to submit):
 ## your code for the webpage and file uploader, your code for the AWS Lamda and SES portion, a video of the system usage).
## [Extra credit] Once all the users have clicked on the link, the file should be deleted.
#### What tools you need to use: Use an AWS EC2 instance to host the webserver for the app. Use AWS S3 to store the file. Use AWS Lambda and AWS SES to send the emails.
#### Use AWS DynamoDB or RDS to store file info.
#### Grading Rubric: EC2 based web server (5 points), File upload and storage (5 points),
#### database usage (5 points), email to users (5 points), [Extra credit] file deletion [4 points].
