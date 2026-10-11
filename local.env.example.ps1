$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "465"
$env:SMTP_USER = "your_email@gmail.com"
$env:SMTP_PASS = "your_16_char_gmail_app_password"
$env:SMTP_FROM = "FloodGuard <your_email@gmail.com>"

# Render Free blocks outbound SMTP. Use Brevo's HTTPS API there instead:
# $env:EMAIL_PROVIDER = "brevo"
# $env:BREVO_API_KEY = "your_brevo_api_key"
# $env:BREVO_FROM_EMAIL = "verified_sender@example.com"
# $env:BREVO_FROM_NAME = "FloodGuard India"

$env:TWILIO_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_TOKEN = "your_twilio_auth_token"
$env:TWILIO_FROM = "+1xxxxxxxxxx"

$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_USER = "root"
$env:DB_PASS = "your_mysql_password"
$env:DB_NAME = "floodguard_db"
