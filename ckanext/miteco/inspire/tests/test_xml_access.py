"""Permission and package/version boundaries without databases or CKAN fixtures."""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from ckan.plugins import toolkit
from ckan.logic import NotFound

PACKAGE={'id':'package-uuid','name':'package-slug','spatial_advanced_xml':'current-hash'}


def test_authorized_package_passes_user_context():
    from ckanext.miteco.inspire import access
    context={'user':'synthetic-member','ignore_auth':False}
    with patch.object(access.toolkit,'get_action') as action:
        action.return_value.return_value=PACKAGE
        assert access.authorized_package(context,'package-slug')==PACKAGE
        action.assert_called_with('package_show')
        args=action.return_value.call_args.args
        assert args[1]=={'id':'package-slug'}
        assert args[0].get('user')=='synthetic-member'
        assert not args[0].get('ignore_auth')


@pytest.mark.parametrize('failure',[toolkit.NotAuthorized,NotFound])
def test_authorization_failures_propagate(failure):
    from ckanext.miteco.inspire import access
    with patch.object(access.toolkit,'get_action') as action:
        action.return_value.side_effect=failure
        with pytest.raises(failure): access.authorized_package({'user':'outsider'},'package-uuid')


@pytest.mark.parametrize('identifier',['package-uuid','package-slug'])
def test_explicit_version_accepts_only_package_identity(identifier):
    from ckanext.miteco.inspire import access
    doc=SimpleNamespace(uuid=identifier,md5='version',xml='<original/>')
    with patch.object(access.insp_model.InspireHandler,'get',return_value=doc):
        assert access.find_document(PACKAGE,'version') is doc


def test_explicit_alien_version_never_falls_back_to_own_xml():
    from ckanext.miteco.inspire import access
    alien=SimpleNamespace(uuid='alien-package',md5='alien-version',xml='<private/>')
    own=SimpleNamespace(uuid=PACKAGE['id'],md5='own-version',xml='<own/>')
    def lookup(uuid=None,md5=None): return alien if md5=='alien-version' else own
    with patch.object(access.insp_model.InspireHandler,'get',side_effect=lookup) as get:
        assert access.find_document(PACKAGE,'alien-version') is None
        assert get.call_count==1


def test_missing_explicit_version_never_falls_back():
    from ckanext.miteco.inspire import access
    with patch.object(access.insp_model.InspireHandler,'get',return_value=None) as get:
        assert access.find_document(PACKAGE,'missing') is None
        assert get.call_count==1


def test_current_pointer_cannot_expose_alien_package():
    from ckanext.miteco.inspire import access
    alien=SimpleNamespace(uuid='alien-package',md5='current-hash',xml='<private/>')
    with patch.object(access.insp_model.InspireHandler,'get',side_effect=lambda uuid=None,md5=None:alien if md5 else None):
        assert access.find_document(PACKAGE) is None


def test_hash_only_authorizes_actual_document_owner():
    from ckanext.miteco.inspire import access
    doc=SimpleNamespace(uuid='owner-uuid',md5='version',xml='<private/>')
    context={'user':'synthetic-member'}
    with patch.object(access.insp_model.InspireHandler,'get',return_value=doc), \
         patch.object(access,'authorized_package',return_value={'id':'owner-uuid','name':'owner-slug'}) as authorize:
        assert access.get_document(context,version='version') is doc
        authorize.assert_called_once_with(context,'owner-uuid')


def test_hash_only_denied_owner_stays_denied():
    from ckanext.miteco.inspire import access
    doc=SimpleNamespace(uuid='private-owner',md5='version')
    with patch.object(access.insp_model.InspireHandler,'get',return_value=doc), \
         patch.object(access,'authorized_package',side_effect=toolkit.NotAuthorized):
        with pytest.raises(toolkit.NotAuthorized): access.get_document({'user':'outsider'},version='version')


def test_id_plus_alien_hash_is_not_found():
    from ckanext.miteco.inspire import access
    with patch.object(access,'authorized_package',return_value=PACKAGE), \
         patch.object(access,'find_document',return_value=None):
        with pytest.raises(NotFound): access.get_document({'user':'member'},identifier='package-uuid',version='alien')


@pytest.mark.parametrize('identifier', ['', 'new'])
def test_new_form_does_not_look_up_a_package(identifier):
    from ckanext.miteco.inspire.blueprint import inspire_form
    with patch('ckanext.miteco.inspire.access.authorized_package') as authorize, \
         patch('ckanext.miteco.inspire.blueprint.toolkit.render', return_value='form') as render:
        assert inspire_form(identifier) == 'form'
        authorize.assert_not_called()
        assert render.call_args.kwargs['extra_vars']['pkg_dict'] == {}


def test_existing_form_uses_authorized_package():
    from ckanext.miteco.inspire.blueprint import inspire_form
    with patch('ckanext.miteco.inspire.access.authorized_package', return_value=PACKAGE) as authorize, \
         patch('ckanext.miteco.inspire.blueprint.toolkit.render', return_value='form') as render:
        assert inspire_form(PACKAGE['id']) == 'form'
        assert authorize.call_args.args[1] == PACKAGE['id']
        assert authorize.call_args.args[0]['ignore_auth'] is False
        assert render.call_args.kwargs['extra_vars']['pkg_dict'] == PACKAGE


@pytest.mark.parametrize('failure,status', [(toolkit.NotAuthorized, 403), (NotFound, 404)])
def test_existing_form_keeps_permission_and_existence_errors(failure, status):
    from ckanext.miteco.inspire.blueprint import inspire_form
    from werkzeug.exceptions import HTTPException
    with patch('ckanext.miteco.inspire.access.authorized_package', side_effect=failure), \
         patch('ckanext.miteco.inspire.blueprint.toolkit.render') as render:
        with pytest.raises(HTTPException) as error:
            inspire_form(PACKAGE['id'])
        assert error.value.code == status
        render.assert_not_called()
