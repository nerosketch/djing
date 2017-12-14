from django.db import models
from django.utils.translation import ugettext_lazy as _
from accounts_app.models import UserProfile
from chatbot.telebot import send_notify


class MessageError(Exception):
    pass


class MessageStatus(models.Model):
    msg = models.ForeignKey('Message', related_name='msg_statuses')
    user = models.ForeignKey(UserProfile, related_name='usr_msg_status')
    MESSAGE_STATES = (
        ('new', _('New')),
        ('old', _('Seen')),
        ('del', _('Deleted'))
    )
    state = models.CharField(max_length=3, choices=MESSAGE_STATES, default='new')

    def __str__(self):
        return "%s for %s (%s)" % (self.get_state_display(), self.user, self.msg)

    class Meta:
        db_table = 'message_status'
        unique_together = (
            ('msg', 'user', 'state')
        )
        verbose_name = _('Message status')
        verbose_name_plural = _('Messages statuses')


class Message(models.Model):
    text = models.TextField(_("Body"))
    sent_at = models.DateTimeField(_("sent at"), auto_now_add=True)
    author = models.ForeignKey(UserProfile, related_name='messages')
    conversation = models.ForeignKey('Conversation', verbose_name=_('Conversation'))
    attachment = models.FileField(upload_to='messages_attachments/%Y_%m_%d', blank=True, null=True)
    account_status = models.ManyToManyField(UserProfile, through=MessageStatus, through_fields=('msg', 'user'))

    def __str__(self):
        return self.text[:9]

    def _set_status(self, account, code):
        try:
            ms = MessageStatus.objects.get(msg=self, user=account)
            if ms.status == code:
                return False
            ms.status = code
            ms.save(update_fields=['status'])
            return True
        except MessageStatus.DoesNotExist:
            return False

    def set_status_old(self, account):
        return self._set_status(account, 'old')

    def set_status_del(self, account):
        return self._set_status(account, 'del')

    def set_status_new(self, account):
        return self._set_status(account, 'new')

    class Meta:
        db_table = 'messages'
        ordering = ['-sent_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        permissions = (
            ('can_view_messages', _('Can view messages')),
        )


class ConversationMembership(models.Model):
    account = models.ForeignKey(UserProfile, related_name='memberships')
    conversation = models.ForeignKey('Conversation')
    PARTICIPANT_STATUS = (
        ('adm', _('Admin')),
        ('gst', _('Guest')),
        ('ban', _('Banned user')),
        ('inv', _('Inviter'))
    )
    status = models.CharField(max_length=3, choices=PARTICIPANT_STATUS, default='gst')
    who_invite_that_user = models.ForeignKey(UserProfile, null=True, blank=True, related_name='self_conversations')

    def __str__(self):
        return "%s < %s" % (self.conversation, self.account)

    class Meta:
        db_table = 'conversation_memberships'
        verbose_name = _("Conversation membership")
        verbose_name_plural = _("Conversation memberships")


def id_to_userprofile(acc):
    if isinstance(acc, UserProfile):
        return acc
    try:
        return UserProfile.objects.get(pk=acc)
    except UserProfile.DoesNotExist:
        raise MessageError(_('Participant profile does not found'))


class ConversationManager(models.Manager):

    def create_conversation(self, author, other_participants, title=None):
        other_participants = [id_to_userprofile(acc) for acc in other_participants]
        if not title:
            usernames = [acc.username for acc in other_participants]
            if not usernames:
                title = _('No name')
            else:
                title = ', '.join(usernames)
        conversation = self.create(title=title, author=author)
        for acc in other_participants:
            ConversationMembership.objects.create(
                account=acc, conversation=conversation, status='adm', who_invite_that_user=author
            )

        ConversationMembership.objects.create(
            account=author, conversation=conversation, status='inv'
        )
        return conversation

    def get_new_messages_count(self, account):
        ms_count = MessageStatus.objects.filter(user=account, state='new').count()
        return ms_count

    def fetch(self, account):
        conversations = self.filter(models.Q(author=account) | models.Q(participants__in=[account])).annotate(
            msg_count=models.Count('message', distinct=True)
        )
        return conversations


class Conversation(models.Model):
    title = models.CharField(max_length=32)
    participants = models.ManyToManyField(UserProfile, related_name='conversations',
                                          through='ConversationMembership',
                                          through_fields=('conversation', 'account'))
    author = models.ForeignKey(UserProfile)
    date_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    objects = ConversationManager()

    def get_messages(self):
        return Message.objects.filter(conversation=self).order_by('sent_at')[:10]

    def get_messages_new_count(self, account):
        msgs = Message.objects.filter(conversation=self)
        return MessageStatus.objects.filter(user=account, msg__in=msgs, state='new').count()

    def last_message(self):
        messages = Message.objects.filter(conversation=self)
        if messages.count() > 0:
            return messages[0]

    def new_message(self, text, attachment, author, with_status=True):
        msg = Message.objects.create(
            text=text, conversation=self, attachment=attachment, author=author
        )
        if with_status:
            for participant in self.participants.all():
                if participant == author:
                    continue
                MessageStatus.objects.create(msg=msg, user=participant)
        send_notify(msg_text=text,account=author, tag='msgapp')
        return msg

    def remove_message(self, msg):
        if isinstance(msg, Message):
            m = msg
        else:
            m = Message.objects.get(pk=int(msg))
        if m is None:
            return False
        else:
            m.delete()
        return True

    def _make_participant_status(self, user, status, cm=None):
        if cm is None:
            cm = ConversationMembership.objects.get(account=user, conversation=self)
        else:
            if not isinstance(cm, ConversationMembership):
                raise TypeError('cm must be instance of msg_app.ConversationMembership')
        cm.status = status
        cm.save(update_fields=['status'])
        return cm

    def make_participant_status_admin(self, user):
        return self._make_participant_status(user, 'adm')

    def make_participant_status_guest(self, user):
        return self._make_participant_status(user, 'gst')

    def make_participant_status_ban(self, user):
        return self._make_participant_status(user, 'ban')

    def make_participant_status_inviter(self, user):
        return self._make_participant_status(user, 'inv')

    def remove_participant(self, user):
        try:
            cm = ConversationMembership.objects.get(account=user, conversation=self)
            cm.delete()
        except ConversationMembership.DoesNotExist:
            pass

    def add_participant(self, author, user):
        return ConversationMembership.objects.create(
            account=user, conversation=self, status='gst', who_invite_that_user=author
        )

    def find_messages_by_text(self, text):
        return Message.objects.filter(text__icontains=text, conversation=self)

    def _make_messages_status(self, account, status):
        qs = MessageStatus.objects.filter(msg__conversation=self, user=account).exclude(state='del')
        if status != 'del':
            qs = qs.exclude(state=status)
        return qs.update(state=status)

    def make_messages_status_new(self, account):
        return self._make_messages_status(account, 'new')

    def make_messages_status_old(self, account):
        return self._make_messages_status(account, 'old')

    class Meta:
        db_table = 'conversations'
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        permissions = (
            ('can_view_conversation', _('Can view conversation')),
        )
