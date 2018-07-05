import re
import time
import _thread
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
projects = ["zh_CN", "zh_TW", "ja_JP"]

# A lock for the database
db_lock = _thread.allocate_lock()


@app.route('/')
def index():
    lang_stat = db_get_lang_stat()
    time_str = db_get_last_updated_time_str()
    return render_template("index.html",
                           lang_stat=lang_stat,
                           time_str=time_str)


@app.route('/lang/<lang>')
def lang_index(lang):
    results = db_get_files_from_lang(lang)
    time_str = db_get_last_updated_time_str()
    return render_template("lang_index.html",
                           results=results,
                           svnweb_url=SVNWEB_URL,
                           time_str=time_str)


@app.route('/init')
def init():
    db.create_all()
    return jsonify({"message": "Init was successful."}), 200


@app.route('/update')
def update():
    if db_lock.locked():
        return jsonify({"message": "An update is in progress, please check later."}), 423
    else:
        _thread.start_new_thread(db_update_data, ())
        return jsonify({"message": "Update was successfully triggered."}), 200


# A decorator
def with_db_lock(func):
    def new_func():
        db_lock.acquire()
        func()
        db_lock.release()
    return new_func


def svn_compare(path, orig_path, regex):
    try:
        orig_rev = str(client.info(rel_path=orig_path)["commit_revision"])
    except svn.exception.SvnException:
        orig_rev = "SVN Error"
    file = client.cat(rel_filepath=path).decode("utf-8", "ignore")
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


def compare_rev(rev, orig_rev):
    if orig_rev == "SVN Error":
        return None, "SVN Error, original file may be moved."
    if rev == "1":
        return None, "Legacy revision (1.X) used, skipping."

    try:
        int_rev = int(rev)
        int_orig_rev = int(orig_rev)
    except ValueError:
        return None, "Revision parse error, skipping."

    if int_rev > int_orig_rev:
        return None, "File revision ahead of original, skipping."
    if int_rev == int_orig_rev:
        return True, "Up to date."
    if int_rev < int_orig_rev:
        return False, "Outdated."


@with_db_lock
def db_update_data():
    details = get_all_file_details()

    # Update Files
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

    # Update Lang
    lang_stat = db_get_lang_from_files()
    for lang, stat in lang_stat.items():
        if Lang.query.filter(Lang.lang == lang).count() == 0:
            db.session.add(Lang(lang=lang))
            db.session.commit()
        db_lang = Lang.query.filter(Lang.lang == lang).first()
        db_lang.updated = stat["updated"]
        db_lang.outdated = stat["outdated"]
        db_lang.ignored = stat["ignored"]
        db.session.commit()

    # Update Meta
    if Meta.query.filter(Meta.key == "last_updated").count() == 0:
        db.session.add(Meta(key="last_updated"))
        db.session.commit()
    db_time = Meta.query.filter(Meta.key == "last_updated").first()
    db_time.value = str(int(time.time()))
    db.session.commit()


def db_get_lang_from_files():
    lang_stat = {}
    files = Files.query.all()

    for file in files:
        if file.lang not in lang_stat.keys():
            lang_stat[file.lang] = {
                "updated": 0,
                "outdated": 0,
                "ignored": 0
            }
        up_to_date, message = compare_rev(file.rev, file.orig_rev)
        if up_to_date is None:
            lang_stat[file.lang]["ignored"] += 1
        elif up_to_date:
            lang_stat[file.lang]["updated"] += 1
        else:
            lang_stat[file.lang]["outdated"] += 1

    return lang_stat


def db_get_files_from_lang(lang):
    results = {}

    files = Files.query.filter(Files.lang == lang).all()
    for file in files:
        if file.lang not in results.keys():
            results[file.lang] = []
        up_to_date, message = compare_rev(file.rev, file.orig_rev)
        results[file.lang].append({
            "path": file.path,
            "orig_path": file.orig_path,
            "rev": file.rev,
            "orig_rev": file.orig_rev,
            "up_to_date": up_to_date,
            "message": message,
            "diff_url": get_diff_url(file.orig_path, file.rev, file.orig_rev),
            }
        )

    return results


def db_get_lang_stat():
    lang_stat = {}
    if Lang.query.count() == 0:
        raise ValueError("Database has no records.")

    for lang in projects:
        db_lang = Lang.query.filter(Lang.lang == lang).first()
        lang_stat[lang] = {
            "updated": db_lang.updated,
            "outdated": db_lang.outdated,
            "ignored": db_lang.ignored
        }

    return lang_stat


def db_get_last_updated_time_str():
    db_time = Meta.query.filter(Meta.key == "last_updated").first()
    time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(db_time.value)))

    return time_str
