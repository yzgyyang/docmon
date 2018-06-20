import re
import svn.remote

from app import app
from flask import jsonify, request, render_template

# SVN client init
SVN_URL = "https://svn.FreeBSD.org/doc/head/"
SVNWEB_URL = "https://svnweb.FreeBSD.org/doc/head/"
client = svn.remote.RemoteClient(SVN_URL)

# Config
regex = "Original [Rr]evision: r{0,1}([0-9]*)"
projects = ["zh_CN"]


@app.route('/')
def index():
    results = {}

    details = get_all_file_details()
    for lang, files in details.items():
        results[lang] = []
        for file in files:
            file["up_to_date"], file["rev"], file["orig_rev"] = \
                svn_compare(file["path"], file["orig_path"], regex)
            file["diff_url"] = get_diff_url(file["orig_path"], file["rev"], file["orig_rev"])
            print(file)
            results[lang].append(file)

    return render_template("index.html",
                           results=results,
                           svnweb_url=SVNWEB_URL)


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
    try:
        orig_rev = str(client.info(rel_path=orig_path)["commit_revision"])
    except svn.exception.SvnException:
        orig_rev = "SVN Error"
    file = client.cat(rel_filepath=path).decode("utf-8")
    re_result = re.search(regex, file)
    if re_result is None:
        return None, "", orig_rev
    rev = re_result.group(1)
    return rev == orig_rev, rev, orig_rev


def get_diff_url(orig_path, rev, orig_rev):
    url = SVNWEB_URL + orig_path + "?r1=" + rev + "&r2=" + orig_rev
    return url


def get_file_line(lang):
    with open("gen/" + lang) as f:
        return f.read().split("\n")


def get_file_detail(file_line):
    if "=>" in file_line:
        path = file_line.split("=>")[0].strip()
        orig_path = file_line.split("=>")[1].strip()
    else:
        path = file_line
        if "htdocs" in path:
            orig_path = "en_US.ISO8859-1/htdocs/"
            orig_path += path.split("htdocs/", 1)[1]
        elif "share/xml" in path:
            orig_path = "share/xml/"
            orig_path += path.split("share/xml/", 1)[1]
        else:
            return None

    detail = {
        "lang": path.split(".", 1)[0],
        "path": path,
        "orig_path": orig_path,
    }

    print(path + " => " + orig_path)
    return detail


def get_all_file_details():
    details = {}

    for lang in projects:
        details[lang] = []
        for line in get_file_line(lang):
            detail = get_file_detail(line)
            if detail is not None:
                details[lang].append(detail)

    return details
