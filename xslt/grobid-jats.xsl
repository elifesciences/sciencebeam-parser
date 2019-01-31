<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:xs="http://www.w3.org/2001/XMLSchema" 
  xmlns:mml="http://www.w3.org/1998/Math/MathML" 
  xmlns:xlink="http://www.w3.org/1999/xlink" 
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="xlink xs mml tei"
  version="1.0"
>
  <xsl:template match="/">
    <article article-type="research-article">
      <xsl:apply-templates select="tei:TEI/tei:teiHeader"/>
      <body/>
      <back>
        <xsl:apply-templates select="tei:TEI/tei:text/tei:back"/>
      </back>
    </article>
  </xsl:template>

  <xsl:template match="tei:teiHeader">
    <front>
      <xsl:if test="tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:monogr/tei:title">
        <journal-meta>
          <journal-title-group>
            <journal-title>
              <xsl:value-of select="tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:monogr/tei:title"/>
            </journal-title>
          </journal-title-group>
        </journal-meta>
      </xsl:if>

      <article-meta>
        <title-group>
          <article-title>
            <xsl:apply-templates select="tei:fileDesc/tei:titleStmt/tei:title"/>
          </article-title>
        </title-group>

        <contrib-group content-type="author">
          <xsl:for-each select="tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:analytic/tei:author">
            <contrib contrib-type="person">
              <xsl:apply-templates select="tei:persName"/>

              <xsl:if test="tei:email">
                <email>
                  <xsl:value-of select="tei:email"/>
                </email>
              </xsl:if>

              <xsl:if test="tei:affiliation">
                <xref ref-type="aff">
                  <xsl:attribute name='rid'>
                    <xsl:value-of select="tei:affiliation/@key"/>
                  </xsl:attribute>
                </xref>
              </xsl:if>
            </contrib>
          </xsl:for-each>
        </contrib-group>

        <xsl:for-each select="tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:analytic/tei:author/tei:affiliation">
          <aff>
            <xsl:attribute name='id'>
              <xsl:value-of select="@key"/>
            </xsl:attribute>
            <xsl:if test="tei:orgName[@type='institution']">
              <institution content-type="orgname">
                <xsl:value-of select="tei:orgName[@type='institution']"/>
              </institution>
            </xsl:if>
            <xsl:if test="tei:orgName[@type='department']">
              <institution content-type="orgdiv1">
                <xsl:value-of select="tei:orgName[@type='department']"/>
              </institution>
            </xsl:if>
            <xsl:if test="tei:orgName[@type='laboratory']">
              <institution content-type="orgdiv2">
                <xsl:value-of select="tei:orgName[@type='laboratory']"/>
              </institution>
            </xsl:if>
            <xsl:if test="tei:address/tei:settlement">
              <city>
                <xsl:value-of select="tei:address/tei:settlement"/>
              </city>
            </xsl:if>
            <xsl:if test="tei:address/tei:country">
              <country>
                <xsl:value-of select="tei:address/tei:country"/>
              </country>
            </xsl:if>
          </aff>
        </xsl:for-each>

        <abstract>
          <xsl:apply-templates select="tei:profileDesc/tei:abstract"/>
        </abstract>
      </article-meta>
    </front>
  </xsl:template>

  <xsl:template match="tei:back">
    <xsl:apply-templates select="tei:div/tei:listBibl"/>
  </xsl:template>

  <xsl:template match="tei:listBibl">
    <xsl:if test="tei:biblStruct">
      <ref-list id="ref-list-1">
        <xsl:apply-templates select="tei:biblStruct"/>
      </ref-list>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:biblStruct">
    <ref>
      <xsl:attribute name='id'>
        <xsl:value-of select="./@xml:id"/>
      </xsl:attribute>

      <element-citation publication-type="journal">
        <xsl:choose>
          <xsl:when test="tei:analytic/tei:title[@type='main']">
            <article-title>
              <xsl:value-of select="tei:analytic/tei:title[@type='main']"/>
            </article-title>
          </xsl:when>
          <xsl:when test="tei:monogr/tei:title[@type='main']">
            <article-title>
              <xsl:value-of select="tei:monogr/tei:title[@type='main']"/>
            </article-title>
          </xsl:when>
        </xsl:choose>

        <xsl:if test="tei:monogr/tei:title[@level='j']">
          <source>
            <xsl:value-of select="tei:monogr/tei:title[@level='j']"/>
          </source>
        </xsl:if>

        <xsl:if test="tei:monogr/tei:imprint/tei:date[@type='published']">
          <xsl:call-template name="parseDateComponents">
            <xsl:with-param name="date" select="tei:monogr/tei:imprint/tei:date[@type='published']/@when"/>
          </xsl:call-template>
        </xsl:if>

        <xsl:if test="tei:monogr/tei:imprint/tei:biblScope[@unit='volume']">
          <volume>
            <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='volume']"/>
          </volume>
        </xsl:if>

        <xsl:if test="tei:monogr/tei:imprint/tei:biblScope[@unit='issue']">
          <issue>
            <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='issue']"/>
          </issue>
        </xsl:if>

        <xsl:choose>
          <xsl:when test="tei:monogr/tei:imprint/tei:biblScope[@unit='page'][@from or @to]">
            <xsl:if test="tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@from">
              <fpage>
                <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@from"/>
              </fpage>
            </xsl:if>

            <xsl:if test="tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@to">
              <lpage>
                <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@to"/>
              </lpage>
            </xsl:if>
          </xsl:when>
          <xsl:when test="tei:monogr/tei:imprint/tei:biblScope[@unit='page']/text()">
            <fpage>
              <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='page']"/>
            </fpage>
            <lpage>
              <xsl:value-of select="tei:monogr/tei:imprint/tei:biblScope[@unit='page']"/>
            </lpage>
          </xsl:when>
        </xsl:choose>

        <xsl:if test="tei:monogr/tei:idno[@type='doi']">
          <pub-id pub-id-type="doi">
            <xsl:value-of select="tei:monogr/tei:idno[@type='doi']"/>
          </pub-id>
        </xsl:if>

        <xsl:if test="tei:analytic/tei:author/tei:persName">
          <person-group person-group-type="author">
            <xsl:apply-templates select="tei:analytic/tei:author/tei:persName"/>
          </person-group>
        </xsl:if>

        <xsl:if test="tei:monogr/tei:author/tei:persName">
          <person-group person-group-type="author">
            <xsl:apply-templates select="tei:monogr/tei:author/tei:persName"/>
          </person-group>
        </xsl:if>
      </element-citation>
    </ref>
  </xsl:template>

  <xsl:template match="tei:persName">
    <name>
      <surname>
        <xsl:value-of select="tei:surname"/>
      </surname>
      <given-names>
        <xsl:for-each select="tei:forename">
          <xsl:if test="position() > 1">
            <xsl:value-of select="' '"/>
          </xsl:if>
          <xsl:value-of select="string(.)"/>
        </xsl:for-each>
      </given-names>
    </name>
  </xsl:template>

  <xsl:template match="tei:title">
    <xsl:apply-templates select="node()"/>
  </xsl:template>

  <xsl:template match="tei:p">
    <p>
      <xsl:apply-templates select="node()|@*"/>
    </p>
  </xsl:template>

  <!--
  Template: parseDateComponents (XSLT 1.0)

  Params:
    date: ISO year, year-month or year-month-day
  
  Examples:
    date=2001 => <year>2001</year>
    date=2001-02 => <year>2001</year><month>02</month>
    date=2001-02-03 => <year>2001</year><month>02</month><day>03</day>
  -->
  <xsl:template name="parseDateComponents">
    <xsl:param name="date" select="."/>
    <xsl:call-template name="_parseDateComponentYearMonthDay">
      <xsl:with-param name="value" select="$date"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_parseDateComponentYearMonthDay">
    <xsl:param name="value" select="."/>
    <xsl:choose>
      <xsl:when test="contains($value, '-')">
        <year>
          <xsl:value-of select="substring-before($value, '-')"/>
        </year>
        <xsl:call-template name="_parseDateComponentMonthDay">
          <xsl:with-param name="value" select="substring-after($value, '-')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <year>
          <xsl:value-of select="$value"/>
        </year>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_parseDateComponentMonthDay">
    <xsl:param name="value" select="."/>
    <xsl:choose>
      <xsl:when test="contains($value, '-')">
        <month>
          <xsl:value-of select="substring-before($value, '-')"/>
        </month>
        <day>
          <xsl:value-of select="substring-after($value, '-')"/>
        </day>
      </xsl:when>
      <xsl:otherwise>
        <month>
          <xsl:value-of select="$value"/>
        </month>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>