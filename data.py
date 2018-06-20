PROJECTS = {
    "zh_CN": {
        "config": {
            "htdocs": {
                "path_prefix": "zh_CN.UTF-8/htdocs/",
                "orig_path_prefix": "en_US.ISO8859-1/htdocs/",
                "rev_type": "comment",
                "regex": "Original [Rr]evision: r([0-9]*)",
            },
            "share_xml": {
                "path_prefix": "zh_CN.UTF-8/share/xml/",
                "orig_path_prefix": "share/xml/",
                "rev_type": "comment",
                "regex": "Original [Rr]evision: r([0-9]*)",
            }
        },
        "files": {
            "htdocs": [{
                "path": "index.xsl",
                "orig_path": "index.xsl",
            }, {
                "path": "where.xml",
                "orig_path": "where.xml",
            }, {
                "path": "community.xsl",
                "orig_path": "community.xsl",
            }],
            "share_xml": [{
                "path": "news.xml",
                "orig_path": "news.xml",
            }, {
                "path": "header.l10n.ent",
                "orig_path": "header.ent",
            }]
        }
    }
}
