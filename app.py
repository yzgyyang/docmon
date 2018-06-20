#!env/bin/python
import re
import svn.remote

from flask import Flask, jsonify, request

# Flask init
app = Flask(__name__)

# SVN client init
SVN_URL = "https://svn.FreeBSD.org/doc/head"
client = svn.remote.RemoteClient(SVN_URL)


EN_URL = "share/xml/news.xml"
CN_URL = "zh_CN.UTF-8/share/xml/news.xml"
REGEX_CN_COMMIT = "Original Revision: r([0-9]*)"


@app.route('/')
def index():
    return jsonify({"message": "Hello world! Please use /api."}), 200


@app.route('/api', methods=['GET'])
def api():
    path = request.args.get("path")
    ref_path = request.args.get("ref_path")
    regex = request.args.get("regex")
    if None in (path, ref_path, regex):
        return jsonify({"message": "Missing one of (path, ref_path, regex)"}), 400

    file = client.cat(rel_filepath=path).decode("utf-8")
    rev = re.search(regex, file).group(1)
    ref_rev = str(client.info(rel_path=ref_path)["commit_revision"])
    return jsonify({"rev": rev,
                    "ref_rev": ref_rev}), 200


if __name__ == '__main__':
    app.run(debug=True)