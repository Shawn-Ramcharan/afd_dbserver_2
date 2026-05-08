import uuid
import enum
# import boto3
from sqlalchemy import Enum as SqlaEnum
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.schema import UniqueConstraint, PrimaryKeyConstraint
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Column, select)
from .mixin import IdMixin, BaseMixin, AttrMixin, ProjectScopedDataMixin, ProjectScopedAssocMixin
from .project import Project

if TYPE_CHECKING:
    from .take_select import TakeSelect

class ETakeSelectListType(enum.Enum):
    order = "order"
    wishlist = "wishlist"
    generic = "generic"


class TakeSelectListAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "take_select_list_assoc_t"
    __table_args__ = (
        PrimaryKeyConstraint(
            "id",
            "take_select_list_id",
            "take_select_id",
            name="pk_take_select_list_assoc_t",
        ),
    )
    take_select_list_id: uuid.UUID = Field(foreign_key="take_select_list_t.id")
    take_select_list: "TakeSelectList" = Relationship()
    take_select_id: uuid.UUID = Field(foreign_key="take_select_t.id")
    take_select: "TakeSelect" = Relationship()

class TakeSelectList(
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    SQLModel,
    table=True,
):
    """The TakeSelectList holds a list of TakeSelects for use, primarily, with
    client ordering. There are three types of list - 'order' and 'wishlist' for
    client ordering, and 'generic' for use in select post processing.

    The object keesps track of VirtualAsset placeholder names in the arbitrary
    attrs.  This is also where list-specific actions, such as enabling or
    disabling entries in the TakeSelect's CaptureLoad are tracked.

    The attrs are also used to store info such as when the list was submitted
    (if it is an order) and when that submission was confirmed by Animatrik.

    It's worth noting that a single TakeSelect can appear in multiple lists as
    the client may not order all the CaptureLoadEntries in a TakeSelect at the
    same time.

    """

    __tablename__ = "take_select_list_t"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            "type_",
            name="take_select_list_project_id_name_type_uix",
        ),
    )
    name: Optional[str] = Field(max_length=128, default=None)
    type_: ETakeSelectListType = Field(
        sa_column=Column(
            SqlaEnum(ETakeSelectListType, name="etakeselectlisttype"), nullable=False
        )
    )
    is_editable: Optional[bool] = Field(default=True)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Optional[Project] = Relationship(
        back_populates="take_select_lists")
    take_selects: list["TakeSelect"] = Relationship(
        link_model=TakeSelectListAssoc,
        back_populates="take_select_lists",
    )
    PROJECT_ASSOC_CLS: ClassVar = TakeSelectListAssoc
    PROJECT_CLS_ATTR: ClassVar = "take_select_list_id"

    @classmethod
    def create(cls, payload: SQLModel, dbsession: DBSession):
        if payload.name is None or payload.name == "":
            # get the count of number of lists this project already has
            stmt = select(TakeSelectList).where(
                TakeSelectList.project_id == payload.project_id,
                TakeSelectList.type_ == payload.type_
            )
            list_count = dbsession.exec(stmt).count()
            new_list_name = "{0} #{1:03d}".format(str(payload.type_).title(), list_count+1)
            payload.name = new_list_name
        model = super(TakeSelectList, cls).create(payload, dbsession)
        return model

    @classmethod
    def get_all(
            cls,
            dbsession: DBSession,
            project_id: uuid.UUID,
            type_: ETakeSelectListType | None = None
    ):
        if type_ is None:
            stmt = select(TakeSelectList).where(
                TakeSelectList.project_id == project_id
            )
        elif type_ not in ETakeSelectListType.__members__:
            raise ValueError(f"Invalid type {type_}. Check ETakeSelectListType.")
        else:
            stmt = select(TakeSelectList).where(
                TakeSelectList.project_id == project_id,
                TakeSelectList.type_ == type_
            )
        results = dbsession.exec(stmt).all()#.order_by(
            # TakeSelectList.last_modified.desc())).all()
        return results

    def add_take_selects(self, dbsession: DBSession, take_select_ids: list[uuid.UUID]):
        from .take_select import TakeSelect
        stmt = select(TakeSelect).where(TakeSelect.id.in_(take_select_ids))
        take_selects = dbsession.exec(stmt).all()
        for take_select in take_selects:
            if take_select not in self.take_selects:
                self.take_selects.append(take_select)
        self.update_stamp(dbsession)

    def remove_take_selects(self, dbsession: DBSession, take_select_ids: list[uuid.UUID]):
        from .take_select import TakeSelect
        stmt = select(TakeSelect).where(TakeSelect.id.in_(take_select_ids))
        take_selects = dbsession.exec(stmt).all()
        for take_select in take_selects:
            if take_select not in self.take_selects:
                self.take_selects.remove(take_select)
        self.update_stamp(dbsession)

    # def place_order(self, dbsession: DBSession, request):
    #     self.is_editable = False
    #     for take_select in self.take_selects:
    #         take_select.is_editable = False
    #         take_select.update_stamp(dbsession)
    #     self.update_stamp(dbsession)
    #     dbsession.commit()
    #     aws_sns_arn = request.registry.settings.get("aws.sns.arn")
    #     aws_access_key = request.registry.settings.get("aws.access_key")
    #     aws_secret_key = request.registry.settings.get("aws.secret_key")
    #     # LOG.debug("aws.sns.arn: {0}".format(aws_sns_arn))
    #     if (aws_sns_arn is not None) and (aws_access_key is not None) and (aws_secret_key is not None):
    #         self._send_order_notification(aws_sns_arn, aws_access_key, aws_secret_key)
    #     else:
    #         return None
    #         # LOG.warning("Missing AWS credentials for sending order notifications")
    #
    # def _send_order_notification(self, aws_sns_arn, aws_access_key, aws_secret_key):
    #     boto_client = boto3.client(
    #         "sns",
    #         aws_access_key_id=aws_access_key,
    #         aws_secret_access_key=aws_secret_key,
    #         region_name='us-west-2'
    #     )
    #     order_placed_by = self.attrs.get("order_placed_by","unknown")
    #     order_placed_on = self.attrs.get("order_placed_on", "")
    #     order_note = self.attrs.get("order_note", "No note provided")
    #     if order_placed_on != "":
    #         dt = datetime.datetime.strptime(order_placed_on, "%Y-%m-%dT%H:%M:%S.%f")
    #         order_placed_on = dt.strftime("%-d %b %Y @ %-I:%M%p")
    #     # Send notification / Max notification size is 256KB
    #     subject = "[{0}] New order placed: {1} by {2}".format(self.project.code, self.name, order_placed_by)
    #     if aws_sns_arn.endswith("-dev"):
    #         subject = "[DEV SERVER]{0}".format(subject)
    #     selects_text = []
    #     self.take_selects.sort(key=lambda x: x.priority)
    #     priority = None
    #     for take_select in self.take_selects:
    #         if priority != take_select.priority:
    #             priority = take_select.priority
    #             selects_text.append("\tPriority: {0}\n".format(priority))
    #         # get delivery name
    #         delivery_name = take_select.delivery_name
    #         if not delivery_name or delivery_name=='':
    #             delivery_name = take_select.take.delivery_name
    #             if not delivery_name or delivery_name=='':
    #                 delivery_name = take_select.take.name
    #         selects_text.append("\t\t{0}    {1} - {2}    Delivery name: '{3}'\n".format(take_select.take.name, take_select.timecode_range.tc_in, take_select.timecode_range.tc_out, delivery_name))
    #         # check capture load
    #         for entry in take_select.capture_load.entries:
    #             if "replacement_virtual_asset" in entry.attrs:
    #                 selects_text.append("\t\t\t* {0}'s target has been changed to '{2}' (cse_id={1})\n".format(entry.solver_setup.name, entry.id, entry.attrs["replacement_virtual_asset"]["code"]))
    #             if "virtual_asset_placeholder_name" in entry.attrs:
    #                 selects_text.append("\t\t\t* {0} has a placeholder name for a new asset: '{2}' (cse_id={1})\n".format(entry.solver_setup.name, entry.id, entry.attrs["virtual_asset_placeholder_name"]))
    #     seconds_totals_text = "\tBody:\t\t{body}\n\tFace:\t\t{face}\n\tFingers:\t{fingers}\n\tProps:\t\t{props}".format(**self.attrs.get("seconds_totals",{"body": "","face": "","fingers": "","props": ""}))
    #     payload = """{0} on {1}\n\nClient note:{2}\nTakeSelectList Id: {3}\n\nSeconds totals:\n{4}\n\nSelects:\n{5}""".format(subject, order_placed_on, order_note, self.id, seconds_totals_text, "".join(selects_text))
    #     # Debug - keep track of length of SNS payload (256KB max)
    #     payload += "\n\n<Debug len={0}>".format(len(payload.encode('utf-8')))
    #     LOG.debug(payload)
    #     try:
    #         result = boto_client.publish( 
    #                     Subject=subject,
    #                     Message=payload, 
    #                     TopicArn=aws_sns_arn
    #                     )
    #     except ClientError as err:
    #         LOG.error(err)
    #         raise HTTPServiceUnavailable("I'm sorry, there's something wrong with this service right now.  Please contact Animatrik.")
    #     else:
    #         LOG.debug("Place Order SNS message sent to subscribers: {0}".format(result))
    #
    #
    #
