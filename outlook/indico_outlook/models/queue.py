from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


class OutlookAction(int, IndicoEnum):
    add = 1
    update = 2
    remove = 3


class OutlookQueueEntry(db.Model):
    """Pending calendar updates"""
    __tablename__ = 'queue'
    __table_args__ = (db.Index(None, 'user_id', 'event_id', 'action'),
                      {'schema': 'plugin_outlook'})

    #: Entry ID (mainly used to sort by insertion order)
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: :class:`OutlookAction` to perform
    action = db.Column(
        PyIntEnum(OutlookAction),
        nullable=False
    )

    #: The user associated with the queue entry
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'outlook_queue',
            lazy='dynamic'
        )
    )
    #: The Event this queue entry is associated with
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'outlook_queue_entries',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return '<OutlookQueueEntry({}, {}, {}, {})>'.format(self.id, self.event_id, self.user_id,
                                                            OutlookAction(self.action).name)

    @classmethod
    def record(cls, event, user, action):
        """Records a new calendar action

        :param event: the event (a :class:`.Event` instance)
        :param user: the user (a :class:`.User` instance)
        :param action: the action (an :class:`OutlookAction` member)
        """
        # It would be nice to delete matching records first, but this sometimes results in very weird deadlocks
        event.outlook_queue_entries.append(cls(user_id=user.id, action=action))
        db.session.flush()
