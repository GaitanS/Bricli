"""
Views for messaging system
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from accounts.models import CraftsmanProfile

from .models import Conversation, Message, create_conversation, send_message


@login_required
@require_POST
@csrf_protect
def send_contact_message(request, craftsman_id):
    """
    Trimite un mesaj de contact către un meșter
    """
    craftsman = get_object_or_404(CraftsmanProfile, id=craftsman_id)

    subject = request.POST.get("subject", "").strip()
    message_content = request.POST.get("message", "").strip()

    if not subject or not message_content:
        messages.error(request, "Toate câmpurile sunt obligatorii.")
        return redirect("accounts:craftsman_detail", slug=craftsman.slug)

    # Creează conversația și trimite mesajul
    try:
        conversation = create_conversation(
            user1=request.user, user2=craftsman.user, subject=subject, related_craftsman=craftsman
        )

        send_message(sender=request.user, recipient=craftsman.user, content=message_content, conversation=conversation)

        messages.success(
            request,
            f"Mesajul a fost trimis către {craftsman.display_name}. "
            'Vei primi răspunsul în secțiunea "Mesajele mele".',
        )

    except Exception:
        messages.error(request, "A apărut o eroare la trimiterea mesajului. Te rugăm să încerci din nou.")

    return redirect("accounts:craftsman_detail", slug=craftsman.slug)


class ConversationListView(LoginRequiredMixin, ListView):
    """
    Lista conversațiilor utilizatorului
    """

    model = Conversation
    template_name = "messaging/conversation_list.html"
    context_object_name = "conversations"
    paginate_by = 20

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related("participants", "messages")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Numără mesajele necitite
        unread_count = Message.objects.filter(recipient=self.request.user, is_read=False).count()

        context["unread_count"] = unread_count
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """
    Detaliile unei conversații cu mesajele
    """

    model = Conversation
    template_name = "messaging/conversation_detail.html"
    context_object_name = "conversation"

    def get_queryset(self):
        # Doar conversațiile în care utilizatorul este participant
        return Conversation.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()

        # Obține mesajele conversației
        messages = conversation.messages.select_related("sender", "recipient").all()
        context["messages"] = messages

        # Obține celălalt participant
        other_participant = conversation.get_other_participant(self.request.user)
        context["other_participant"] = other_participant

        # Marchează mesajele ca citite
        conversation.mark_as_read(self.request.user)

        return context


@login_required
@require_POST
@csrf_protect
def send_reply(request, conversation_id):
    """
    Trimite un răspuns într-o conversație existentă
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    message_content = request.POST.get("message", "").strip()

    if not message_content:
        messages.error(request, "Mesajul nu poate fi gol.")
        return redirect("messaging:conversation_detail", pk=conversation_id)

    # Găsește destinatarul (celălalt participant)
    recipient = conversation.get_other_participant(request.user)

    if not recipient:
        messages.error(request, "Nu s-a putut găsi destinatarul.")
        return redirect("messaging:conversation_detail", pk=conversation_id)

    try:
        send_message(sender=request.user, recipient=recipient, content=message_content, conversation=conversation)

        messages.success(request, "Răspunsul a fost trimis.")

    except Exception:
        messages.error(request, "A apărut o eroare la trimiterea răspunsului.")

    return redirect("messaging:conversation_detail", pk=conversation_id)


@login_required
def mark_conversation_read(request, conversation_id):
    """
    Marchează o conversație ca citită (AJAX)
    """
    if request.method == "POST":
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

        conversation.mark_as_read(request.user)

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})


@login_required
def get_unread_count(request):
    """
    Returnează numărul de mesaje necitite (AJAX)
    """
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return JsonResponse({"unread_count": unread_count})
