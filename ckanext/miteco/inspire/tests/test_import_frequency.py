"""Import-only frequency filtering follows the active CKAN schema."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from ckanext.miteco.inspire.schema import filter_import_frequency

ALLOWED='http://publications.europa.eu/resource/authority/frequency/ANNUAL'
REJECTED='http://publications.europa.eu/resource/authority/frequency/NOT_PLANNED'
SCHEMA={'dataset_fields':[{'field_name':'frequency','choices':[{'value':ALLOWED}]}]}


def test_allowed_frequency_and_extras_unchanged():
    data={'frequency':ALLOWED,'extras':[{'key':'other','value':'kept'}]}; before=deepcopy(data)
    with patch('ckanext.miteco.inspire.schema.toolkit.get_action') as action:
        action.return_value.return_value=SCHEMA
        assert filter_import_frequency({'user':'synthetic'},data)==[]
        assert data==before
        action.assert_called_once_with('scheming_dataset_schema_show')
        action.return_value.assert_called_once_with({'user':'synthetic'},{'type':'dataset'})


def test_unrepresentable_frequency_is_omitted_with_warning_and_no_extra_backdoor():
    data={'frequency':REJECTED,'extras':[{'key':'frequency','value':REJECTED},{'key':'other','value':'kept'},{'key':'frequency','value':'duplicate'}]}
    with patch('ckanext.miteco.inspire.schema.toolkit.get_action') as action, \
         patch('ckanext.miteco.inspire.schema.toolkit._',side_effect=lambda x:x):
        action.return_value.return_value=SCHEMA
        warnings=filter_import_frequency({},data)
    assert 'frequency' not in data
    assert data['extras']==[{'key':'other','value':'kept'}]
    assert len(warnings)==1 and warnings[0]['field']=='frequency' and warnings[0]['value']==REJECTED
    assert warnings[0]['message']


@pytest.mark.parametrize('data',[{}, {'frequency':None}, {'frequency':''}])
def test_absent_frequency_does_not_lookup_schema_or_invent_values(data):
    before=deepcopy(data)
    with patch('ckanext.miteco.inspire.schema.toolkit.get_action') as action:
        assert filter_import_frequency({},data)==[]
        action.assert_not_called()
    assert data==before


def test_frequency_with_unrestricted_schema_is_preserved():
    data={'frequency':REJECTED,'type':'custom'}
    with patch('ckanext.miteco.inspire.schema.toolkit.get_action') as action:
        action.return_value.return_value={'dataset_fields':[{'field_name':'frequency'}]}
        assert filter_import_frequency({},data)==[]
        action.return_value.assert_called_once_with({}, {'type':'custom'})
    assert data['frequency']==REJECTED


def test_frequency_not_supported_by_schema_is_omitted():
    data={'frequency':REJECTED}
    with patch('ckanext.miteco.inspire.schema.toolkit.get_action') as action, \
         patch('ckanext.miteco.inspire.schema.toolkit._',side_effect=lambda x:x):
        action.return_value.return_value={'dataset_fields':[]}
        assert filter_import_frequency({},data)[0]['value']==REJECTED
    assert 'frequency' not in data
