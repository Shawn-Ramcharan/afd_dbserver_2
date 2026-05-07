import logging
from typing import ClassVar
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session as DBSession
from sqlmodel import select
from .resource import (
    Resource,
    ResourceAssoc,
    Version,
    Item,
    ItemAssoc
)
LOG = logging.getLogger("afd_dbserver")

class ResourceMixin(object):

    CLS_ID_ATTR: ClassVar = None # example: solver_setup_id

    def get_resource_count(self, dbsession: DBSession, name: str, group: str):
        """ Returns the number of resources with the given name/group that exist for this object.
        """
        # check whether name/group exists for this object
        return self._get_resource_query(dbsession, name, group).count()

    def _get_class_attr(self):
        if self.CLS_ID_ATTR is not None:
            rsc_assoc_cls_id_name = self.CLS_ID_ATTR
        else:
            rsc_assoc_cls_id_name = f"{self.__class__.__name__.lower()}_id"
        return getattr(ResourceAssoc, rsc_assoc_cls_id_name)

    def _get_resource_query(self, dbsession: DBSession, name: str, group: str):
        rsc_assoc_id_col = self._get_class_attr()
        stmt = (
            select(Resource)
            .join(ResourceAssoc)
            .join(self.__class__)
            .where(
                Resource.name == name,
                Resource.group == group,
                rsc_assoc_id_col == self.id
            )
        )
        return dbsession.exec(stmt)

    def _get_owner_uri(self):
        if self.__class__.__name__ == "Project":
            return ""
        elif self.__class__.__name__ == "SolverSetup":
            return f"/solver_setup/{self.name}"
        elif self.__class__.__name__ == "VirtualAssetRevision":
            return f"/virtual_asset/{self.virtual_asset.code}/revision/{self.number}"
        elif self.__class__.__name__ == "Mapping":
            return f"/mapping/{self.fqn}-{self.name}"
        elif self.__class__.__name__ == "Session":
            return f"/session/{self.name}"
        elif self.__class__.__name__ == "Volume":
            return f"/session/{self.session.name}/volume/{self.code}"
        elif self.__class__.__name__ == "Device":
            return f"/session/{self.volume.session.name}/volume/{self.volume.code}/device/{self.code}"
        elif self.__class__.__name__ == "Take":
            return f"/take/{self.name}"
        elif self.__class__.__name__ == "TakeSelect":
            return f"/take_select/{self.id}"

    def _create_resource(
        self,
        dbsession: DBSession,
        user_id: str,
        name: str,
        group: str,
        attrs: dict | None = None
    ):
        """ Creates a new resource.  Does NOT check whether a resource with the same name and group
        already exists.
        """
        project = self.project
        project_id = project.id
        if not attrs:
            attrs = {}
        owner_url = self._get_owner_uri()
        uri = f"adb://project/{project.code}{owner_url}/resource/{name}.{group}"
        resource = Resource(
            name=name,
            group=group,
            uri=uri,
            project_id=project_id,
            created_by=user_id,
            modified_by=user_id,
            attrs=attrs
        )
        dbsession.add(resource)
        dbsession.commit()
        LOG.debug("Created new resource with id: %s"%resource.id)
        attr_name = self._get_class_attr()
        resource_assoc = ResourceAssoc(resource_id=resource.id)
        setattr(resource_assoc, attr_name, self)
        dbsession.add(resource_assoc)
        dbsession.commit()
        return resource

    def create_resource(self,
        dbsession: DBSession,
        user_id: str,
        name, group,
        attrs=None,
        items=None
    ):
        """ Creates a new resource with the given name/group or, if one already exists, returns that.
        """
        LOG.debug(f"name: {name}, group: {group}")
        resource_count = self.get_resource_count(request, name, group)
        LOG.debug(f"resource_count: {resource_count}")
        if resource_count > 1:
            msg = ("Integrity error! It should be impossible "
                "to have more than one name/group combo against "
                f"an object. Found one! {self.__name__} {name}.{group}"
            )
            raise IntegrityError(msg, [], msg)
        if resource_count == 1:
            msg = (f"Unique Constraint! A resource of group ({group}), "
                f"named ({name}) already exists. Use 'update' instead.")
            raise IntegrityError(msg, [], msg)
        if not attrs:
            attrs = {}
        resource = self._create_resource(
            dbsession,
            user_id,
            name,
            group,
            attrs=attrs
        )
        return resource

    def get_resource(self, dbsession: DBSession, name: str, group: str):
        """ Returns the number of resources with the given name/group that exist for this object.
        """
        # check whether name/group exists for this object
        try:
            return self._get_resource_query(dbsession, name, group).one()
        except NoResultFound as _:
            return None
            # raise HTTPNotFound("{0} has no resource matching name={1}, group/{2}".format(self, name, group))

    def get_latest_resources_items_of_group(self, dbsession: DBSession, group: str):
        """ Optimised query for retrieving the latest movie items.
        """
        tag_array = ['latest']
        attr_name = self._get_class_attr()
        stmt = (select(
                Resource.name,
                Version.number,
                ItemAssoc,
                Item
            ).join(ResourceAssoc).join(self.__class__)
            .where(
                attr_name == self.id,
                Resource.group == group,
                Version.resource_id == Resource.id,
                Version.tags.contain(tag_array),
                Version.is_committed is True,
                ItemAssoc.version_id == Version.id,
                ItemAssoc.item_id == Item.id
            )
        )
        results = dbsession.exec(stmt).all()
        data: dict[str, list[ItemAssoc]] = {}
        for result in results:
            name = result[0]
            item_assoc = result[2]
            if name not in data:
                data[name] = []
            data[name].append(item_assoc)
        return data

    def delete_resources(self, dbsession: DBSession):
        """ Deletes all resources associated with this record.
        """
        for resource in self.resources:
            dbsession.delete(resource)
        dbsession.commit()
