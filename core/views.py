from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from properties.models import Property
from agents.models import Agent
from .forms import ContactForm

class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = '/contact/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = [
            {
                'question': 'What are your office hours?',
                'answer': 'Our offices are open Monday through Friday from 9:00 AM to 6:00 PM. We also offer appointments outside regular business hours by request.'
            },
            {
                'question': 'How quickly do you respond to inquiries?',
                'answer': 'We aim to respond to all inquiries within 24 hours during business days. For urgent matters, please call our office directly.'
            },
            {
                'question': 'How can I schedule a property viewing?',
                'answer': 'You can schedule a viewing through our website, by contacting the listing agent directly, or by calling our office. We offer both in-person and virtual tours.'
            },
            {
                'question': 'Do you offer virtual property tours?',
                'answer': 'Yes, we offer virtual tours for most of our properties. You can view these on our property listings or request a live virtual tour with an agent.'
            },
            {
                'question': 'What documents do I need to rent/buy a property?',
                'answer': 'Required documents typically include proof of income, employment verification, photo ID, and references. Specific requirements may vary based on the property and type of transaction.'
            },
            {
                'question': 'Do you help with mortgage arrangements?',
                'answer': 'Yes, we work with several trusted mortgage providers and can help connect you with the right lender for your needs.'
            }
        ]
        
        # Get property and agent info from query parameters
        property_id = self.request.GET.get('property_id')
        agent_id = self.request.GET.get('agent_id')
        
        if property_id:
            context['property'] = Property.objects.filter(id=property_id).first()
        if agent_id:
            context['agent'] = Agent.objects.filter(id=agent_id).first()
            
        return context

    def form_valid(self, form):
        # Get form data
        data = form.cleaned_data
        inquiry_type = data['inquiry_type']
        
        # Prepare email context
        email_context = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'inquiry_type': dict(form.INQUIRY_TYPES).get(inquiry_type),
            'subject': data['subject'],
            'message': data['message'],
            'preferred_contact': data['preferred_contact'],
            'newsletter_signup': data['newsletter_signup']
        }
        
        # Add property/agent info if available
        if data['property_id']:
            try:
                property_obj = Property.objects.get(id=data['property_id'])
                email_context['property'] = property_obj
            except Property.DoesNotExist:
                pass
                
        if data['agent_id']:
            try:
                agent_obj = Agent.objects.get(id=data['agent_id'])
                email_context['agent'] = agent_obj
            except Agent.DoesNotExist:
                pass

        # Send HTML email to admin
        html_content = render_to_string('emails/contact_admin.html', email_context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=f"Contact Form: {inquiry_type.title()} - {data['subject']}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[data['email']]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # Send confirmation email to user
        html_content = render_to_string('emails/contact_confirmation.html', email_context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject="Thank you for contacting Real Estate",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[data['email']]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # Add to newsletter if requested
        if data['newsletter_signup']:
            # Add to newsletter list (implement your newsletter logic here)
            pass

        messages.success(self.request, "Thank you for your message. We'll get back to you soon!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = [
            {
                'name': 'John Smith',
                'position': 'CEO & Founder',
                'bio': 'With over 20 years of experience in real estate, John leads our company with vision and expertise.',
                'image': 'img/team/ceo.jpg'
            },
            {
                'name': 'Sarah Johnson',
                'position': 'Chief Operations Officer',
                'bio': 'Sarah ensures smooth operations and maintains our high standards of service delivery.',
                'image': 'img/team/coo.jpg'
            },
            {
                'name': 'Michael Brown',
                'position': 'Sales Director',
                'bio': 'Michael leads our sales team with innovative strategies and market expertise.',
                'image': 'img/team/sales.jpg'
            }
        ]
        return context 