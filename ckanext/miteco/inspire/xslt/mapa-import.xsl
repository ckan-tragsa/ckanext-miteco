<?xml version="1.0" encoding="UTF-8"?>
<!-- Local overrides of the installed SchemingDCAT mapping; no upstream copy. -->
<xsl:stylesheet version="2.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:gmd="http://www.isotc211.org/2005/gmd"
 xmlns:srv="http://www.isotc211.org/2005/srv"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns:dct="http://purl.org/dc/terms/"
 xmlns:dcat="http://www.w3.org/ns/dcat#"
 xmlns:foaf="http://xmlns.com/foaf/0.1/"
 xmlns:schema="http://schema.org/"
 xmlns:prov="http://www.w3.org/ns/prov#"
 exclude-result-prefixes="gmd srv xlink">
 <xsl:import href="urn:miteco:schemingdcat:custom-transform"/>

 <!-- Keep the base mapping and enrich its primary resource inside the same
      XSLT execution. The XML is not reparsed by another Python mapper. -->
 <xsl:template match="gmd:MD_Metadata|//gmd:MD_Metadata">
  <xsl:variable name="record" select="."/>
  <xsl:variable name="mapped"><xsl:apply-imports/></xsl:variable>
  <xsl:apply-templates select="$mapped/node()" mode="mapa-lineage">
   <xsl:with-param name="record" select="$record" tunnel="yes"/>
  </xsl:apply-templates>
 </xsl:template>

 <xsl:template match="@*|node()" mode="mapa-lineage">
  <xsl:copy><xsl:apply-templates select="@*|node()" mode="mapa-lineage"/></xsl:copy>
 </xsl:template>

 <xsl:template match="rdf:Description[foaf:isPrimaryTopicOf]" mode="mapa-lineage">
  <xsl:param name="record" tunnel="yes"/>
  <xsl:copy>
   <xsl:apply-templates select="@*|node()" mode="mapa-lineage"/>
   <xsl:if test="not($record/gmd:identificationInfo/srv:SV_ServiceIdentification)
                 and $record/gmd:dataQualityInfo/*/gmd:lineage/*/gmd:statement/*[normalize-space() != '']">
    <xsl:for-each select="$record/gmd:dataQualityInfo/*/gmd:lineage/*/*[self::gmd:source or self::gmd:processStep]">
     <xsl:element name="{if (self::gmd:source) then 'dct:source' else 'prov:wasGeneratedBy'}">
      <rdf:Description>
       <schema:position rdf:datatype="http://www.w3.org/2001/XMLSchema#integer"><xsl:value-of select="position()"/></schema:position>
       <dct:description><xsl:value-of select="*/gmd:description/*"/></dct:description>
      </rdf:Description>
     </xsl:element>
    </xsl:for-each>
   </xsl:if>
  </xsl:copy>
 </xsl:template>

 <xsl:template name="CoupledResource" match="gmd:identificationInfo[1]/*/srv:operatesOn">
  <xsl:param name="uriref" select="if (@uriref) then string(@uriref) else if (@xlink:href) then string(@xlink:href) else if (@uuidref) then concat('urn:uuid:',@uuidref) else ''"/>
  <xsl:if test="$uriref != ''">
   <xsl:if test="$profile = $extended and $include-deprecated = 'yes'">
    <dct:hasPart><dcat:Dataset rdf:about="{$uriref}"/></dct:hasPart>
   </xsl:if>
   <dcat:servesDataset><dcat:Dataset rdf:about="{$uriref}"/></dcat:servesDataset>
  </xsl:if>
 </xsl:template>

 <xsl:template name="service-endpoint">
  <xsl:param name="function"/>
  <xsl:param name="protocol"/>
  <xsl:param name="url"/>
  <xsl:param name="endpoint-url" select="$url"/>
  <xsl:param name="endpoint-description" select="$url"/>
  <xsl:param name="service-type"/>
  <xsl:if test="$endpoint-url != ''"><dcat:endpointURL rdf:resource="{$endpoint-url}"/></xsl:if>
  <xsl:if test="$endpoint-description != ''"><dcat:endpointDescription rdf:resource="{$endpoint-description}"/></xsl:if>
 </xsl:template>
</xsl:stylesheet>
