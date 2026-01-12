import argparse
import smtplib
from email.message import EmailMessage

EICAR = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2525)
    parser.add_argument("--sender", default="sender@example.com")
    parser.add_argument("--recipient", default="user@example.com")
    args = parser.parse_args()

    msg = EmailMessage()
    msg["From"] = args.sender
    msg["To"] = args.recipient
    msg["Subject"] = "EICAR test"
    msg.set_content("Test email with EICAR attachment")
    msg.add_attachment(EICAR.encode(), maintype="application", subtype="octet-stream", filename="eicar.txt")

    with smtplib.SMTP(args.host, args.port) as smtp:
        smtp.send_message(msg)
    print("Sent")


if __name__ == "__main__":
    main()
