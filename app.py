#!env/bin/python
import re
import svn.remote

from data import PROJECTS
from flask import Flask, jsonify, request, render_template

# Flask init
app = Flask(__name__)

# SVN client init
SVN_URL = "https://svn.FreeBSD.org/doc/head/"
SVNWEB_URL = "https://svnweb.FreeBSD.org/doc/head/"
client = svn.remote.RemoteClient(SVN_URL)


@app.route('/')
def index():
    results = []

    # Unpacking PROJECTS =>
    # (str)project_name: (dict)(zh_CN, ...)
    for project_name, project in PROJECTS.items():
        lang = project_name

        # Unpacking config =>
        # (str)file_type: (dict)(config)
        for file_type, config in project["config"].items():
            path_prefix = config["path_prefix"]
            orig_path_prefix = config["orig_path_prefix"]
            rev_type = config["rev_type"]
            regex = config["regex"]

            # Unpacking files[filetype] =>
            # (dict)file
            for file in project["files"][file_type]:
                path = path_prefix + file["path"]
                orig_path = orig_path_prefix + file["orig_path"]
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
