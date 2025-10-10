"""
Models for in-platform messaging system
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """
    Conversație între doi utilizatori
    """

    participants = models.ManyToManyField(User, related_name="conversations")
    subject = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Pentru referințe la comenzi/servicii
    related_order = models.ForeignKey(
        "services.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations"
    )
    related_craftsman = models.ForeignKey(
        "accounts.CraftsmanProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations"
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Conversație"
        verbose_name_plural = "Conversații"

    def __str__(self):
        participants_names = ", ".join([p.get_full_name() or p.username for p in self.participants.all()])
        return f"Conversație: {participants_names}"

    def get_other_participant(self, user):
        """Returnează celălalt participant din conversație"""
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        """Returnează ultimul mesaj din conversație"""
        return self.messages.first()

    def mark_as_read(self, user):
        """Marchează toate mesajele ca citite pentru un utilizator"""
        self.messages.filter(recipient=user, is_read=False).update(is_read=True)


class Message(models.Model):
    """
    Mesaj individual într-o conversație
    """

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")

    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Pentru mesaje de sistem (notificări automate)
    is_system_message = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mesaj"
        verbose_name_plural = "Mesaje"

    def __str__(self):
        return f"Mesaj de la {self.sender.username} către {self.recipient.username}"

    def mark_as_read(self):
        """Marchează mesajul ca citit"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])


class MessageAttachment(models.Model):
    """
    Atașamente pentru mesaje (imagini, documente)
    """

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="message_attachments/")
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Atașament mesaj"
        verbose_name_plural = "Atașamente mesaje"

    def __str__(self):
        return f"Atașament: {self.filename}"


class MessageTemplate(models.Model):
    """
    Template-uri pentru mesaje automate de sistem
    """

    TEMPLATE_TYPES = [
        ("order_created", "Comandă creată"),
        ("quote_received", "Ofertă primită"),
        ("quote_accepted", "Ofertă acceptată"),
        ("order_completed", "Comandă finalizată"),
        ("review_request", "Cerere recenzie"),
    ]

    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Template mesaj"
        verbose_name_plural = "Template-uri mesaje"

    def __str__(self):
        return f"Template: {self.get_template_type_display()}"


# Utility functions for messaging
def create_conversation(user1, user2, subject="", related_order=None, related_craftsman=None):
    """
    Creează o conversație între doi utilizatori
    """
    # Verifică dacă există deja o conversație între acești utilizatori
    existing_conversation = Conversation.objects.filter(participants=user1).filter(participants=user2).first()

    if existing_conversation:
        return existing_conversation

    # Creează conversația nouă
    conversation = Conversation.objects.create(
        subject=subject, related_order=related_order, related_craftsman=related_craftsman
    )
    conversation.participants.add(user1, user2)

    return conversation


def send_message(sender, recipient, content, conversation=None, is_system_message=False):
    """
    Trimite un mesaj între doi utilizatori
    """
    if not conversation:
        conversation = create_conversation(sender, recipient)

    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        recipient=recipient,
        content=content,
        is_system_message=is_system_message,
    )

    # Actualizează timestamp-ul conversației
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])

    return message


def send_system_message(recipient, template_type, context=None):
    """
    Trimite un mesaj automat de sistem
    """
    try:
        template = MessageTemplate.objects.get(template_type=template_type, is_active=True)

        # TODO: Implementează formatarea template-ului cu context
        content = template.content
        if context:
            content = content.format(**context)

        # Creează un utilizator de sistem pentru mesajele automate
        system_user, created = User.objects.get_or_create(
            username="system",
            defaults={"email": "system@bricli.ro", "first_name": "Sistem", "last_name": "Bricli", "is_active": False},
        )

        return send_message(sender=system_user, recipient=recipient, content=content, is_system_message=True)

    except MessageTemplate.DoesNotExist:
        return None
