import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from commons.logs import get_logger
from commons.get_config import get_config as global_get_config

logger = get_logger("email_module")
global_config = global_get_config()

MODULES_BASE = global_config["directories"]["modules"]

class Email:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config

        logger.info(f"[EMAIL] Context at init: {self.context.get_all()}")
        logger.info(f"[EMAIL] Initializing Email module with config: {self.config}")

        # SMTP settings
        self.smtp_host = self.config.get("smtp_host") or os.getenv("SMTP_HOST")
        self.smtp_port = int(self.config.get("smtp_port", 587))
        self.smtp_user = self.config.get("smtp_user") or os.getenv("SMTP_USER")
        self.smtp_pass = self.config.get("smtp_pass") or os.getenv("SMTP_PASS")
        self.from_addr = self.config.get("from_addr", "noreply@example.com")

        if not self.smtp_host:
            logger.warning("[EMAIL] SMTP host not configured. Emails will fail to send.")

        logger.debug(f"[EMAIL] SMTP config: host={self.smtp_host}, port={self.smtp_port}, user={self.smtp_user}, from={self.from_addr}")

        # Template engine
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(MODULES_BASE, "email_module", "templates")),
            autoescape=True
        )

    def send_email(self, to, subject, body=None, template=None, html=True):
        logger.info(f"[EMAIL] Sending to: {to}, subject: {subject}")
        context = self.context.get_all()

        if not to or not subject:
            return {
                "status": "fail",
                "message": "Missing required 'to' or 'subject' fields",
                "data": None
            }

        # Render email body
        try:
            if template:
                template_file = f"{template}.j2" if not template.endswith((".j2", ".html")) else template
                logger.info(f"[EMAIL] Using template: {template_file}")
                rendered_body = self.jinja_env.get_template(template_file).render(context=context)
            elif body:
                rendered_body = body
            else:
                return {
                    "status": "fail",
                    "message": "Either 'body' or 'template' must be provided",
                    "data": None
                }
        except Exception as e:
            logger.error(f"[EMAIL] Template rendering failed: {e}")
            return {
                "status": "fail",
                "message": f"Failed to render template: {e}",
                "data": None
            }

        # Prepare MIME message
        try:
            if html:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(rendered_body, "html"))
            else:
                msg = MIMEText(rendered_body, "plain")

            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = to if isinstance(to, str) else ", ".join(to)
        except Exception as e:
            logger.error(f"[EMAIL] Failed to compose message: {e}")
            return {
                "status": "fail",
                "message": f"Email composition failed: {e}",
                "data": None
            }

        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_pass:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.from_addr, to, msg.as_string())

            logger.info(f"[EMAIL] Email successfully sent to {to}")
            return {
                "status": "ok",
                "message": f"Email sent successfully to {to}",
                "data": {
                    "to": to,
                    "subject": subject
                }
            }

        except Exception as e:
            logger.error(f"[EMAIL] Failed to send email: {e}")
            return {
                "status": "fail",
                "message": f"Failed to send email: {e}",
                "data": None
            }
