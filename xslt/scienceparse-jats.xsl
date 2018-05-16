<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:xs="http://www.w3.org/2001/XMLSchema" 
  xmlns:mml="http://www.w3.org/1998/Math/MathML" 
  xmlns:xlink="http://www.w3.org/1999/xlink" 
  xmlns:tei="http://www.tei-c.org/ns/1.0" exclude-result-prefixes="xlink xs mml tei" version="1.0">

  <xsl:template match="/root">
    <article article-type="research-article">
      <xsl:call-template name="front"/>
      <xsl:call-template name="body"/>
      <xsl:call-template name="back"/>
    </article>
  </xsl:template>

  <xsl:template name="front">
    <front>
      <article-meta>
        <xsl:if test="title">
          <title-group>
            <article-title>
              <xsl:value-of select="title"/>
            </article-title>
          </title-group>
        </xsl:if>

        <xsl:call-template name="authors"/>

        <xsl:if test="abstractText">
          <abstract>
            <xsl:value-of select="abstractText"/>
          </abstract>
        </xsl:if>
      </article-meta>
    </front>
  </xsl:template>

  <xsl:template name="authors">
    <contrib-group content-type="author">
      <xsl:for-each select="authors/item">
        <contrib contrib-type="person">
          <xsl:if test="name">
            <xsl:call-template name="parseName">
              <xsl:with-param name="name" select="name"/>
            </xsl:call-template>
          </xsl:if>
        </contrib>
      </xsl:for-each>
    </contrib-group>
  </xsl:template>

  <xsl:template name="back">
    <back>
      <xsl:call-template name="references"/>
    </back>
  </xsl:template>

  <xsl:template name="references">
    <xsl:if test="references">
      <ref-list id="ref-list-1">
        <xsl:for-each select="references/item">
          <xsl:call-template name="reference"/>
        </xsl:for-each>
      </ref-list>
    </xsl:if>
  </xsl:template>

  <xsl:template name="reference">
    <ref>
      <xsl:attribute name='id'>
        <xsl:value-of select="'ref-'"/>
        <xsl:value-of select="position()"/>
      </xsl:attribute>

      <element-citation publication-type="journal">
        <xsl:if test="title">
          <article-title>
            <xsl:value-of select="title"/>
          </article-title>
        </xsl:if>

        <xsl:if test="year">
          <year>
            <xsl:value-of select="year"/>
          </year>
        </xsl:if>

        <xsl:if test="venue">
          <source>
            <xsl:value-of select="venue"/>
          </source>
        </xsl:if>

        <xsl:if test="authors/item">
          <person-group person-group-type="author">
            <xsl:for-each select="authors/item">
              <xsl:call-template name="parseName">
                <xsl:with-param name="name" select="."/>
              </xsl:call-template>
            </xsl:for-each>
          </person-group>
        </xsl:if>
      </element-citation>
    </ref>
  </xsl:template>

  <xsl:template name="body">
    <body>
      <xsl:call-template name="sections"/>
    </body>
  </xsl:template>

  <xsl:template name="sections">
    <xsl:if test="sections">
      <xsl:for-each select="sections/item">
        <xsl:call-template name="section"/>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

  <xsl:template name="section">
    <sec>
      <xsl:attribute name='id'>
        <xsl:value-of select="'sec-'"/>
        <xsl:value-of select="position()"/>
      </xsl:attribute>

      <xsl:if test="heading">
        <title>
          <xsl:value-of select="heading"/>
        </title>
      </xsl:if>
      <xsl:if test="text">
        <p>
          <xsl:value-of select="text"/>
        </p>
      </xsl:if>
    </sec>
  </xsl:template>

  <!--
  Template: parseName (XSLT 1.0)

  Params:
    name: full name

  Examples:
    name=Doh => <name><surname>Doh</surname></name>
    name=John Doh => <name><given-names>John</given-names><surname>Doh</surname></name>
    name=John T. Doh => <name><given-names>John T.</given-names><surname>Doh</surname></name>
  -->
  <xsl:template name="parseName">
    <xsl:param name="name" select="."/>
    <name>
      <xsl:choose>
        <xsl:when test="contains($name, ' ')">
          <given-names>
            <xsl:call-template name="substring-before-last">
              <xsl:with-param name="arg" select="$name" />
              <xsl:with-param name="delim" select="' '" />
            </xsl:call-template>
          </given-names>
          <surname>
            <xsl:call-template name="substring-after-last">
              <xsl:with-param name="arg" select="$name" />
              <xsl:with-param name="delim" select="' '" />
            </xsl:call-template>
          </surname>
        </xsl:when>
        <xsl:otherwise>
          <surname>
            <xsl:value-of select="$name"/>
          </surname>
        </xsl:otherwise>
      </xsl:choose>
    </name>
  </xsl:template>

  <xsl:template name="substring-before-last">
    <xsl:param name="arg" select="''" />
    <xsl:param name="delim" select="''" />

    <xsl:if test="$arg != '' and $delim != ''">
      <xsl:variable name="head" select="substring-before($arg, $delim)" />
      <xsl:variable name="tail" select="substring-after($arg, $delim)" />
      <xsl:value-of select="$head" />
      <xsl:if test="contains($tail, $delim)">
        <xsl:value-of select="$delim" />
        <xsl:call-template name="substring-before-last">
          <xsl:with-param name="arg" select="$tail" />
          <xsl:with-param name="delim" select="$delim" />
        </xsl:call-template>
      </xsl:if>
    </xsl:if>
  </xsl:template>

  <xsl:template name="substring-after-last">
    <xsl:param name="arg" select="''" />
    <xsl:param name="delim" select="''" />

    <xsl:if test="$arg != '' and $delim != ''">
      <xsl:variable name="head" select="substring-before($arg, $delim)" />
      <xsl:variable name="tail" select="substring-after($arg, $delim)" />
      <xsl:choose>
        <xsl:when test="contains($tail, $delim)">
          <xsl:call-template name="substring-after-last">
            <xsl:with-param name="arg" select="$tail" />
            <xsl:with-param name="delim" select="$delim" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$tail" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>