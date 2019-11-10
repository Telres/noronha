# -*- coding: utf-8 -*-

from abc import ABC

from noronha.api.utils import ProjResolver, DefaultValidation
from noronha.db.main import Documented, SmartBaseDoc
from noronha.db.proj import Project, Projected
from noronha.common.annotations import Interactive, Scoped, Validated, validate
from noronha.common.logging import LOG


class NoronhaAPI(Documented, Interactive, Projected, Scoped, Validated, ABC):
    
    valid = DefaultValidation
    
    def __init__(self, proj: Project = None, scope: str = None, interactive: bool = False):
        
        self.proj = proj
        Scoped.__init__(self, scope=scope)
        Interactive.__init__(self, interactive=interactive)
    
    class Scope(object):
        
        """Static marker that indicates where the API was called from"""
        
        PYTHON = "Directly instantiating the Python API"
        REST = "HTTP request to a REST API endpoint"
        CLI = "User input to command line interface"
        DEFAULT = PYTHON
        ALL = [PYTHON, REST, CLI]
    
    def set_proj(self, ref_to_proj: str = None, proj_resolvers: list = ()):
        
        self.proj = ProjResolver()(ref_to_proj, proj_resolvers)
        return self
    
    def info(self, **kwargs):
        
        return self.doc.find_one(**kwargs).pretty()
    
    def rm(self, **kwargs):
        
        if 'target' in kwargs:
            target = kwargs.pop('target')
            assert isinstance(target, SmartBaseDoc)
        else:
            target = self.doc.find_one(**kwargs)
        
        target.delete()
        return {
            'Removed {}'.format(self.doc.__name__):
            target.show()
        }
    
    def lyst(self, _filter: dict = None, **kwargs):
        
        return self.doc.objects(__raw__=_filter or {}, **kwargs)
    
    @validate(_duplicate_filter=(dict, None))
    def new(self, _replace: bool = None, _duplicate_filter=None, **kwargs):
        
        if _duplicate_filter is not None and len(self.doc.objects(**_duplicate_filter)) > 0:
            LOG.warn("{} exists".format(self.doc.__name__))
            
            if _replace is None:
                self._decide("Would you like to overwrite it?", default=True, interrupt=True)
                _replace = True
        
        return self.doc(**kwargs).save(force_insert=not _replace)
    
    def replace(self, **kwargs):
        
        return self.new(_replace=True, **kwargs)
    
    @validate(filter_kwargs=dict, update_kwargs=dict)
    def update(self, filter_kwargs, update_kwargs):
        
        target = self.doc.find_one(**filter_kwargs)
        target.update(**update_kwargs)
        return target.reload()
