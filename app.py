#!env/bin/python
import re
import svn.remote

from flask import Flask, jsonify

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
    file = client.cat(rel_filepath=CN_URL).decode("utf-8")
    trans_version = re.search(REGEX_CN_COMMIT, file).group(1)
    origin_version = str(client.info(rel_path=EN_URL)["commit_revision"])
    return jsonify({"trans_version": trans_version,
                    "origin_version": origin_version}), 201


# log = client.log_default(rel_filepath=EN_URL)


if __name__ == '__main__':
    app.run(debug=True)