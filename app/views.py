import re
import time
import svn.remote

from app import app, db
from flask import jsonify, request, render_template

from app.models import Meta, Lang, Files

# SVN client init
SVN_URL = "https://svn.FreeBSD.org/doc/head/"
SVNWEB_URL = "https://svnweb.FreeBSD.org/doc/head/"
client = svn.remote.RemoteClient(SVN_URL)

# Config
regex = "Original [Rr]evision: r{0,1}([0-9]*)"
projects = ["zh_CN", "zh_TW"]


@app.route('/')
def index():
    results, time_str = db_get_data()
    return render_template("index.html",
                           results=results,
                           svnweb_url=SVNWEB_URL)


@app.route('/init')
def init():
    db.create_all()
    return jsonify({"message": "Init was successful."}), 200


@app.route('/update')
def update():
    db_update_data()
    return jsonify({"message": "Update was successful."}), 200


def svn_compare(path, orig_path, regex):
    try:
        orig_rev = str(client.info(rel_path=orig_path)["commit_revision"])
    except svn.exception.SvnException:
        orig_rev = "SVN Error"
    file = client.cat(rel_filepath=path).decode("utf-8")
    re_result = re.search(regex, file)
    if re_result is None:
        return "", orig_rev
    rev = re_result.group(1)
    return rev, orig_rev


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


def update_data():
    results = {}

    details = get_all_file_details()
    for lang, files in details.items():
        results[lang] = []
        for file in files:
            rev, orig_rev = svn_compare(file["path"], file["orig_path"], regex)
            up_to_date = rev == orig_rev
            file["up_to_date"], file["rev"], file["orig_rev"] = up_to_date, rev, orig_rev
            file["diff_url"] = get_diff_url(file["orig_path"], file["rev"], file["orig_rev"])
            print(file)
            results[lang].append(file)

    return results


def db_update_data():
    details = get_all_file_details()
    for lang, files in details.items():
        for file in files:
            path = file["path"]
            if Files.query.filter(Files.path == path).count() == 0:
                db.session.add(Files(path=path))
                db.session.commit()
            db_file = Files.query.filter(Files.path == path).first()
            db_file.lang = lang
            db_file.orig_path = file["orig_path"]
            db_file.rev, db_file.orig_rev = svn_compare(path, db_file.orig_path, regex)
            db.session.commit()

    if Meta.query.filter(Meta.key == "last_updated").count() == 0:
        db.session.add(Meta(key="last_updated"))
        db.session.commit()
    db_time = Meta.query.filter(Meta.key == "last_updated").first()
    db_time.value = str(int(time.time()))
    db.session.commit()


def db_get_data():
    results = {}
    if Files.query.count() == 0:
        db_update_data()

    files = Files.query.all()
    for file in files:
        if file.lang not in results.keys():
            results[file.lang] = []
        results[file.lang].append({
            "path": file.path,
            "orig_path": file.orig_path,
            "rev": file.rev,
            "orig_rev": file.orig_rev,
            "up_to_date": file.rev == file.orig_rev,
            "diff_url": get_diff_url(file.orig_path, file.rev, file.orig_rev),
            }
        )

    db_time = Meta.query.filter(Meta.key == "last_updated").first()
    time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(db_time.value)))

    return results, time_str
