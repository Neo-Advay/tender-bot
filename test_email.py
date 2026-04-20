from notifications.email import send_email

send_email(
    subject="[Tender Bot] Test Email",
    text_body="This is a test email from Tender Bot.",
)

print("Test email function executed.")