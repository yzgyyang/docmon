from app import db


class Meta(db.Model):
    __tablename__ = 'meta'

    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)


class Lang(db.Model):
    __tablename__ = 'lang'

    lang = db.Column(db.String, primary_key=True)
    updated = db.Column(db.Integer)
    outdated = db.Column(db.Integer)
    ignored = db.Column(db.Integer)


class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    lang = db.Column(db.String)
    path = db.Column(db.String)
    orig_path = db.Column(db.String)
    rev = db.Column(db.String)
    orig_rev = db.Column(db.String)
