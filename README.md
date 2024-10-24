<p align="center">
  <picture>
    <img src="ckanext/miteco/public/images/default/miteco_logo2.png" style="height:150px">
  </picture>
</p>
<h1 align="center">ckanext-miteco - CKAN enhancement</h1>
<p align="center">
<a href="https://github.com/OpenDataGIS/ckanext-miteco/actions/workflows/test.yml"><img src="https://github.com/OpenDataGIS/ckanext-miteco/actions/workflows/test.yml/badge.svg?branch=develop" alt="ckanext-miteco tests"></a>

<p align="center">
    <a href="#overview">Overview</a> •
    <a href="#requirements">Requirements</a> •
    <a href="#improvements">Improvements</a> •
    <a href="#installation">Installation</a> •
    <a href="#tests">Tests</a> •
    <a href="#releasing-a-new-version-of-ckanext-miteco">Release</a> •
    <a href="#license">License</a>
</p>

## Overview
`ckanext-miteco` extension is a tool designed to extend and customise the CKAN metadata and Open Data catalogue for the Spanish Ministry for Ecological Transition and Demographic Challenge ([MITECO](https://www.miteco.gob.es/)). This extension provides specific and thematic functionalities that allow a better management, visualisation and analysis of data related to the ecological transition and the demographic challenge. 

## TODO: Requirements
### Compatibility
Compatibility with core CKAN versions:

| CKAN version | Compatible?     |
|--------------|-----------------|
| 2.8          | ❔ Not tested  |
| 2.9          | ✅ Yes |
| 2.10         | ✅ Yes |

### Plugins
`ckanext-miteco` needs the following extensions:

* [`mjanez/ckanext-dcat`](https://github.com/mjanez/ckanext-dcat):
  ````bash
  pip install -e git+https://github.com/mjanez/ckanext-dcat.git@v1.6.0#egg=ckanext-dcat
  pip install -r ./src/ckanext-dcat/requirements.txt
  ````

* [`ckanext-scheming`](https://github.com/ckan/ckanext-scheming):
  ```bash
  pip install -e git+https://github.com/ckan/ckanext-scheming.git@release-3.0.0#egg=ckanext-scheming
  pip install -r ./src/ckanext-schemingdcat/requirements.txt
  ```

* [`ckanext-spatial`](https://github.com/ckan/ckanext-spatial):
  ```bash
  pip install -e git+https://github.com/ckan/ckanext-spatial.git@v2.1.1#egg=ckanext-spatial
  pip install -r ./src/ckanext-spatial/requirements.txt
  ```

* [`mjanez/ckanext-schemingdcat`](https://github.com/mjanez/ckanext-schemingdcat):
  ```bash
  pip install -e git+https://github.com/mjanez/ckanext-schemingdcat.git@v3.0.0#egg=ckanext_schemingdcat
  pip install -r ./src/ckanext-schemingdcat/requirements.txt
  ```

And modify `ckan.ini`, You can use the default values:
 ```ini
 ckan.plugins = "... spatial_metadata spatial_query resource_proxy geo_view geojson_view wmts_view shp_view dcat schemingdcat_datasets schemingdcat_groups schemingdcat_organizations miteco schemingdcat"
 ```

## TODO: Improvements
`ckanext-miteco` tries to merge ckan and MITECO styles, it might be a good idea to store the values used in  CSS directives were stored in CSS variables, so that `ckanext-miteco` could call them to override CKAN could call them to override CKAN styles, and changes made by the design team without having to rewrite them in the extension.

1. ...
2. ...
3. ...

## Installation

To install ckanext-miteco:

1. Activate your CKAN virtual environment, e.g.

    `. /usr/lib/ckan/default/bin/activate`

2. Clone the source and install it on the `virtualenv`

    ```
    git clone https://github.com/OpenDataGIS/ckanext-miteco.git
    cd ckanext-miteco
    pip install -e .
	pip install -r requirements.txt
    ```

3. Add `miteco` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).
   		
4. Add `miteco` specific configuration to the CKAN config file

5. Restart CKAN.


## TODO: Config settings
At CKAN config .ini file (in `/etc/ckan/default` dir), into the [app:main] 
section, add:

```ini
ckan.site_logo=/images/default/logo_miteco.jpg
ckan.site_title="MITECO SIG CKAN - Des"
ckan.site_description="MITECO SIG CKAN - Des"
ckan.site_intro_text="[#en#] [![MITECO](https://sede.mapa.gob.es/portal/marm/images/common/logo_miteco.jpg#center)](https://miteco.gob.es/) \
    [![ckan-docker-spatial](https://img.shields.io/badge/ckan--docker--spatial-CKAN%202.9.11-brightgreen?style=social&logo=github#center)](https://github.com/mjanez/ckan-docker) \
    The open data portal of the [**Ministry for the Ecological Transition and the Demographic Challenge**](https://www.miteco.gob.es/) consists of an application using CKAN technology for the distribution of maps, data and spatial metadata and a \
    [**CSW Catalog**]({{ {{ pycsw_url }} }}) (OGC standard) for the metadata publication and discovery about spatial resources on the web. \
    [#es#] [![MITECO](https://sede.mapa.gob.es/portal/marm/images/common/logo_miteco.jpg#center)](https://miteco.gob.es/) \
    [![ckan-docker-espacial](https://img.shields.io/badge/ckan--docker--spatial-CKAN%202.9.11-brightgreen?style=social&logo=github#center)](https://github.com/mjanez/ckan-docker) \
    El portal de datos abiertos del [**Ministerio para la Transición Ecológica y el Reto Demográfico**](https://www.miteco.gob.es/) es una aplicación que utiliza la tecnología CKAN para la distribución de mapas, datos y metadatos espaciales y un \
    [**Catálogo CSW**]({{ {{ pycsw_url }} }}) (estándar OGC) para la publicación y descubrimiento de metadatos sobre recursos espaciales en la web."
ckan.site_about="[#en#] [![MITECO](https://sede.mapa.gob.es/portal/marm/images/common/logo_miteco.jpg#center)](https://miteco.gob.es/) \
    [![ckan-docker-spatial](https://img.shields.io/badge/ckan--docker--spatial-CKAN%202.9.11-brightgreen?style=social&logo=github#center)](https://github.com/mjanez/ckan-docker) \
    The open data portal of the [**Ministry for the Ecological Transition and the Demographic Challenge**](https://www.miteco.gob.es/) consists of an application using CKAN technology for the distribution of maps, data and spatial metadata and a \
    [**CSW Catalog**]({{ {{ pycsw_url }} }}) (OGC standard) for the metadata publication and discovery about spatial resources on the web. \
    [#es#] [![MITECO](https://sede.mapa.gob.es/portal/marm/images/common/logo_miteco.jpg#center)](https://miteco.gob.es/) \
    [![ckan-docker-espacial](https://img.shields.io/badge/ckan--docker--spatial-CKAN%202.9.11-brightgreen?style=social&logo=github#center)](https://github.com/mjanez/ckan-docker) \
    El portal de datos abiertos del [**Ministerio para la Transición Ecológica y el Reto Demográfico**](https://www.miteco.gob.es/) es una aplicación que utiliza la tecnología CKAN para la distribución de mapas, datos y metadatos espaciales y un \
    [**Catálogo CSW**]({{ {{ pycsw_url }} }}) (estándar OGC) para la publicación y descubrimiento de metadatos sobre recursos espaciales en la web."
```

And in order to replace the default CKAN favicon with the desired, change the appropriate key:

```ini
ckan.favicon=/images/default/favicon.ico
```

breadcrumbs are shown in the same order that are defined in the key's value

## Developer installation
To install ckanext-miteco for development, activate your CKAN `virtualenv` and
do:

```bash
git clone https://github.com/OpenDataGIS/ckanext-miteco.git
cd ckanext-miteco
python setup.py develop
pip install -r dev-requirements.txt
```

## Tests
Be sure that ckan user has write rights in the root dir of the extension 
(perhaps ckanext-miteco?). If that is not the case and if for security or other 
reasons you can't do it, create a .pytest_cache dir at the root dir of the
extension and make it writable by the ckan user.

To run the tests, at `ckanext-miteco` root dir do:

```bash
pip install -r dev-requirements.txt
pytest --ckan-ini=test.ini
```

To have a more verbose test, you can do:

```bash
pytest -vv --ckan-ini=test.ini`
```

This will give you a few deprecation warnings. You can ignore those about
code outside the extension. Ckan needs a very specific versions of the python
libs it uses, so please do not mess upgrading libs in order to supress the
warnings. Just ignore them.

## Releasing a new version of ckanext-miteco
If ckanext-miteco should be available on PyPI you can follow these steps to 
publish a new version:

1. Update the version number in the `setup.py` file. See 
   [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) 
   for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

	  ```bash
      pip install --upgrade setuptools wheel twine
      ```

3. Create a source and binary distributions of the new version:

	  ```bash
      python setup.py sdist bdist_wheel && twine check dist/*
      ```

   Fix any errors you get.

4. Upload the source distribution to PyPI:

	  ```bash
      twine upload dist/*
      ```

5. Commit any outstanding changes:

	  ```bash
      git commit -a
	  git push
      ```

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:
   
	```bash
	  git tag 0.0.1
	  git push --tags
	```

## License
[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
