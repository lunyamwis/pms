from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Message, Notification, PropertyInquiry

class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'messaging/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user, is_archived=False).order_by('-created_at')

class SentMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'messaging/sent.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user).order_by('-created_at')

class ArchivedMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'messaging/archived.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user, is_archived=True).order_by('-created_at')

class ComposeMessageView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = 'messaging/compose.html'
    fields = ['recipient', 'subject', 'content']
    success_url = reverse_lazy('messaging:sent')

    def form_valid(self, form):
        form.instance.sender = self.request.user
        messages.success(self.request, 'Message sent successfully!')
        return super().form_valid(form)

class ConversationView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'messaging/conversation.html'
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = self.get_object()
        context['conversation'] = Message.objects.filter(
            subject=message.subject,
            sender__in=[message.sender, message.recipient],
            recipient__in=[message.sender, message.recipient]
        ).order_by('created_at')
        return context

class DeleteMessageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        if request.user in [message.sender, message.recipient]:
            message.delete()
            messages.success(request, 'Message deleted successfully!')
        return redirect('messaging:inbox')

class ArchiveMessageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        if request.user == message.recipient:
            message.is_archived = True
            message.save()
            messages.success(request, 'Message archived successfully!')
        return redirect('messaging:inbox')

class MarkMessageReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        if request.user == message.recipient:
            message.is_read = True
            message.save()
        return redirect('messaging:inbox')

class MarkMessageUnreadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        if request.user == message.recipient:
            message.is_read = False
            message.save()
        return redirect('messaging:inbox')

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'messaging/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read!')
        return redirect('messaging:notifications')

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('messaging:notifications')
