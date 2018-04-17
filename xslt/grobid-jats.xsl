<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:xs="http://www.w3.org/2001/XMLSchema" 
	xmlns:mml="http://www.w3.org/1998/Math/MathML" 
	xmlns:xlink="http://www.w3.org/1999/xlink" 
	xmlns:tei="http://www.tei-c.org/ns/1.0"
	exclude-result-prefixes="xlink xs mml tei"
	version="1.0">

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
				<xsl:value-of select="./@id"/>
			</xsl:attribute>

			<element-citation publication-type="journal">
				<xsl:if test="tei:monogr/tei:title">
					<article-title><xsl:value-of select="tei:monogr/tei:title"/></article-title>
				</xsl:if>
				<xsl:if test="tei:monogr/tei:imprint/tei:date[@type='published']">
					<year><xsl:value-of select="tei:monogr/tei:imprint/tei:date[@type='published']/@when"/></year>
				</xsl:if>
				<xsl:if test="tei:monogr/tei:idno[@type='doi']">
					<pub-id pub-id-type="doi"><xsl:value-of select="tei:monogr/tei:idno[@type='doi']"/></pub-id>
				</xsl:if>
				<xsl:if test="tei:note[@type='report_type']">
					<source><xsl:value-of select="tei:note[@type='report_type']"/></source>
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
					<xsl:if test="position() > 1" xml:space="preserve"> </xsl:if>
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
</xsl:stylesheet>