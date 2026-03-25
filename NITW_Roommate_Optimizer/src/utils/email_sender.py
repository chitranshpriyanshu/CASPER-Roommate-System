import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body):
    sender = "your_email@gmail.com"
    password = "your_app_password"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)