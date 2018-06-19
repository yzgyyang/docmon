import re

import svn.remote

SVN_DOC_URL = "https://svn.FreeBSD.org/doc/head"

EN_URL = "share/xml/news.xml"
CN_URL = "zh_CN.UTF-8/share/xml/news.xml"
REGEX_CN_COMMIT = "Original Revision: r([0-9]*)"

if __name__ == "__main__":
    client = svn.remote.RemoteClient(SVN_DOC_URL)

    log = client.log_default(rel_filepath=EN_URL)

    file = client.cat(rel_filepath=CN_URL).decode("utf-8")
    cn_version = re.search(REGEX_CN_COMMIT, file).group(1)
    print(cn_version)

    en_version = client.info(rel_path=EN_URL)["commit_revision"]
    print(en_version)
