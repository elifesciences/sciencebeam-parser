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
			<back/>
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
							<name>
								<surname>
									<xsl:value-of select="tei:persName/tei:surname"/>
								</surname>
								<given-names>
									<xsl:for-each select="tei:persName/tei:forename">
										<xsl:value-of select="string(.)"/>
									</xsl:for-each>
								</given-names>
							</name>

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
						<institution content-type="orgname">
							<xsl:value-of select="tei:orgName[@type='institution']"/>
						</institution>
						<city>
							<xsl:value-of select="tei:address/tei:settlement"/>
						</city>
						<country>
							<xsl:value-of select="tei:address/tei:country"/>
						</country>
					</aff>
				</xsl:for-each>

				<abstract>
					<xsl:apply-templates select="tei:profileDesc/tei:abstract"/>
				</abstract>
			</article-meta>
		</front>
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