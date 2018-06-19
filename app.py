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


EN_URL = "share/xml/news.xml"
CN_URL = "zh_CN.UTF-8/share/xml/news.xml"
REGEX_CN_COMMIT = "Original Revision: r([0-9]*)"


@app.route('/')
def index():
    up_to_date, rev, orig_rev = compare(CN_URL, EN_URL, REGEX_CN_COMMIT)
    path, orig_path = CN_URL, EN_URL
    diff_url = get_diff_url(orig_path, rev, orig_rev)
    lang = get_lang(path)
    results = [{"lang": lang,
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

    is_updated, rev, orig_rev = compare(path, orig_path, regex)
    return jsonify({"rev": rev,
                    "orig_rev": orig_rev}), 200


def compare(path, orig_path, regex):
    file = client.cat(rel_filepath=path).decode("utf-8")
    rev = re.search(regex, file).group(1)
    orig_rev = str(client.info(rel_path=orig_path)["commit_revision"])
    return rev == orig_rev, rev, orig_rev


def get_diff_url(orig_path, rev, orig_rev):
    url = SVNWEB_URL + orig_path + "?r1=" + rev + "&r2=" + orig_rev + "&pathrev=" + orig_rev
    return url


def get_lang(path):
    lang = path.split("/")[0].split(".")[0]
    return lang


if __name__ == '__main__':
    app.run(debug=True)