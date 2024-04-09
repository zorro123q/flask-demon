from extensions import db
from datetime import datetime


class StudentORM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Enum('M', 'F'))
    mobile = db.Column(db.String(11), nullable=False, unique=True)
    class_name = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(255))
    disable = db.Column(db.Boolean, default=False)
    is_del = db.Column(db.Boolean, default=False)

    create_at = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)