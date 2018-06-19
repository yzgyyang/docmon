#!env/bin/python
import re
import svn.remote

from flask import Flask, jsonify, request, render_template

# Flask init
app = Flask(__name__)

# SVN client init
SVN_URL = "https://svn.FreeBSD.org/doc/head/"
SVNWEB_URL = "https://svnweb.FreeBSD.org/doc/head/"
client = svn.remote.RemoteClient(SVN_URL)


# Data
PROJECTS = {
    "zh_CN": {
        "config": {
            "regex": "Original [Rr]evision: r([0-9]*)",
        },
        "files": [{
            "path": "zh_CN.UTF-8/share/xml/news.xml",
            "orig_path": "share/xml/news.xml",
        }, {
            "path": "zh_CN.UTF-8/share/xml/header.l10n.ent",
            "orig_path": "share/xml/header.ent"
        }, {
            "path": "zh_CN.UTF-8/htdocs/index.xsl",
            "orig_path": "en_US.ISO8859-1/htdocs/index.xsl"
        }, {
            "path": "zh_CN.UTF-8/htdocs/where.xml",
            "orig_path": "en_US.ISO8859-1/htdocs/where.xml"
        }, {
            "path": "zh_CN.UTF-8/htdocs/community.xsl",
            "orig_path": "en_US.ISO8859-1/htdocs/community.xsl"
        }]
    }
}


@app.route('/')
def index():
    results = []
    for key, value in PROJECTS.items():
        lang = key
        regex = value["config"]["regex"]
        for file in value["files"]:
            path = file["path"]
            orig_path = file["orig_path"]
            up_to_date, rev, orig_rev = svn_compare(path, orig_path, regex)
            diff_url = get_diff_url(orig_path, rev, orig_rev)
            results += [{"lang": lang,
                         "up_to_date": up_to_date,
                         "path": path,
                         "orig_path": orig_path,
                         "rev": rev,
                         "orig_rev": orig_rev,
                         "diff_url": diff_url}]
    return render_template("index.html", results=results)


@app.route('/api', methods=['GET'])
def api():
    path = request.args.get("path")
    orig_path = request.args.get("orig_path")
    regex = request.args.get("regex")
    if None in (path, orig_path, regex):
        return jsonify({"message": "Missing one of (path, ref_path, regex)"}), 400

    is_updated, rev, orig_rev = svn_compare(path, orig_path, regex)
    return jsonify({"rev": rev,
                    "orig_rev": orig_rev}), 200


def svn_compare(path, orig_path, regex):
    orig_rev = str(client.info(rel_path=orig_path)["commit_revision"])
    file = client.cat(rel_filepath=path).decode("utf-8")
    re_result = re.search(regex, file)
    if re_result is None:
        return None, "", orig_rev
    rev = re_result.group(1)
    return rev == orig_rev, rev, orig_rev


def get_diff_url(orig_path, rev, orig_rev):
    url = SVNWEB_URL + orig_path + "?r1=" + rev + "&r2=" + orig_rev + "&pathrev=" + orig_rev
    return url


if __name__ == '__main__':
    app.run(debug=True)