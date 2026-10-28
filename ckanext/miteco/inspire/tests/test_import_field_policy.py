"""Imported invalid fields preserve editorial values without weakening normal edits."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from ckanext.miteco.inspire.schema import omit_invalid_import_value


def context(**values):
    return dict({'preserve_mapped_fields':True,'_inspire_pushing':True,'_inspire_warnings':[]},**values)


def invoke(key,data,errors,ctx):
    with patch('ckanext.miteco.inspire.schema.toolkit._',side_effect=lambda x:x):
        omit_invalid_import_value(key,data,errors,ctx)


@pytest.mark.parametrize('ctx',[{}, {'preserve_mapped_fields':True}, {'_inspire_pushing':True}, {'preserve_mapped_fields':True,'_inspire_pushing':True}])
def test_normal_edits_or_missing_warning_channel_preserve_errors(ctx):
    key=('access_rights',);data={key:'bad'};errors={key:['Invalid']};before=deepcopy((data,errors,ctx))
    invoke(key,data,errors,ctx)
    assert (data,errors,ctx)==before


def test_valid_value_is_never_replaced():
    key=('created',);data={key:'2025-01-01'};errors={key:[]};ctx=context(_inspire_existing_pkg={'created':'2020-01-01'})
    invoke(key,data,errors,ctx)
    assert data[key]=='2025-01-01' and not ctx['_inspire_warnings']


def test_invalid_new_field_becomes_none_and_warns_only_for_its_error():
    key=('representation_type',);other=('title',);data={key:'bad',other:''};errors={key:['Invalid choice'],other:['Required']};ctx=context()
    invoke(key,data,errors,ctx)
    assert data[key] is None and errors[key]==[] and errors[other]==['Required']
    warning=ctx['_inspire_warnings'][0]
    assert warning['field']=='representation_type' and warning['value']=='bad' and warning['message']


def test_invalid_field_restores_authorized_existing_editorial_value():
    key=('access_rights',);data={key:'bad'};errors={key:['Invalid choice']};ctx=context(_inspire_existing_pkg={'access_rights':'editorial'})
    invoke(key,data,errors,ctx)
    assert data[key]=='editorial' and errors[key]==[]


def test_resource_identity_uses_id_even_when_resources_reordered():
    key=('resources',0,'rights');data={key:'bad',('resources',0,'id'):'second'};errors={key:['Invalid choice']}
    ctx=context(_inspire_existing_pkg={'resources':[{'id':'first','rights':'wrong'},{'id':'second','rights':'editorial'}]})
    invoke(key,data,errors,ctx)
    assert data[key]=='editorial' and errors[key]==[]
    assert ctx['_inspire_warnings'][0]['field']=='resources.0.rights'


@pytest.mark.parametrize('rid',[None,'unknown'])
def test_new_resource_cannot_inherit_value_by_list_position(rid):
    key=('resources',0,'rights');data={key:'bad',('resources',0,'id'):rid};errors={key:['Invalid choice']}
    ctx=context(_inspire_existing_pkg={'resources':[{'id':'first','rights':'must-not-copy'}]})
    invoke(key,data,errors,ctx)
    assert data[key] is None


def test_other_nested_error_is_not_suppressed():
    key=('contact',0,'email');data={key:'bad'};errors={key:['Invalid']};ctx=context()
    invoke(key,data,errors,ctx)
    assert errors[key]==['Invalid'] and data[key]=='bad' and not ctx['_inspire_warnings']


def test_warning_is_not_duplicated_for_repeated_same_failure():
    key=('created',);data={key:'bad'};errors={key:['Invalid']};ctx=context()
    invoke(key,data,errors,ctx)
    data[key]='bad';errors[key]=['Invalid']
    invoke(key,data,errors,ctx)
    assert len(ctx['_inspire_warnings'])==1
