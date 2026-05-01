
class TakeSelect(Base, BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin):
    """ 
    """
    __tablename__ = "take_select_t"
    __table_args__ = ( UniqueConstraint('take_id', 'timecode_range_id', name='take_select_take_timecode_range_uix'), )
    delivery_name = Column(String(128))
    description = Column(Text)
    priority = Column(Integer)
    is_editable = Column(Boolean, default=True)
    take_id = Column(ForeignKey("take_t.id"), nullable=False)
    take = relationship("Take", back_populates="take_selects", lazy='joined')
    project_id = Column(ForeignKey("project_t.id"), nullable=False)
    project = relationship("Project", back_populates="take_selects")
    capture_load_id = Column(ForeignKey("capture_load_t.id"))
    capture_load = relationship("CaptureLoad", lazy='joined')
    timecode_range_id = Column(ForeignKey("timecode_range_t.id"))
    timecode_range = relationship("TimecodeRange", lazy='joined')
    notes = relationship("Note", secondary="note_assoc_t", order_by=desc(text("note_t.last_modified")))
    resources = relationship("Resource", secondary="resource_assoc_t", backref="take_selects")
    take_select_lists = relationship("TakeSelectList", "take_select_list_assoc_t", back_populates="take_selects", lazy='joined')

