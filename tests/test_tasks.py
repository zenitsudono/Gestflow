import pytest
from django.core import mail
from apps.notifications.tasks import (
    send_welcome_email,
    send_notification_email,
    generate_monthly_report,
    export_resources_excel
)
from apps.notifications.models import Notification
from tests.conftest import UserFactory, ResourceFactory

@pytest.mark.django_db
def test_send_welcome_email_task(db_roles):
    user = UserFactory(role=db_roles['user'], email="welcome@gestiflow.com")
    
    # Run task synchronously
    send_welcome_email(str(user.id))
    
    # Verify mail outbox
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["welcome@gestiflow.com"]
    assert "Welcome" in email.subject

@pytest.mark.django_db
def test_send_notification_email_task(db_roles):
    user = UserFactory(role=db_roles['user'], email="notif@gestiflow.com")
    notification = Notification.objects.create(
        recipient=user,
        type='email',
        title="Alert Title",
        message="Alert Content"
    )
    
    send_notification_email(str(notification.id))
    
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["notif@gestiflow.com"]
    assert email.subject == "Alert Title"
    assert email.body == "Alert Content"

@pytest.mark.django_db
def test_generate_monthly_report_task(db_roles):
    user = UserFactory(role=db_roles['user'], email="reporter@gestiflow.com")
    # Create a resource created in the current month
    ResourceFactory(owner=user)
    
    import datetime
    today = datetime.date.today()
    
    generate_monthly_report(str(user.id), today.month, today.year)
    
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["reporter@gestiflow.com"]
    assert len(email.attachments) == 1
    assert email.attachments[0][0] == f"Monthly_Report_{today.month}_{today.year}.pdf"
    assert email.attachments[0][2] == "application/pdf"

@pytest.mark.django_db
def test_export_resources_excel_task(db_roles):
    user = UserFactory(role=db_roles['user'], email="exporter@gestiflow.com")
    ResourceFactory(owner=user, title="Exportable Resource")
    
    export_resources_excel(str(user.id))
    
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["exporter@gestiflow.com"]
    assert len(email.attachments) == 1
    assert email.attachments[0][0] == "resources_export.xlsx"
    assert email.attachments[0][2] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
