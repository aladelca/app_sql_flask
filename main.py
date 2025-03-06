from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from pyarrow.lib import Schema
from sqlalchemy import text
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 60}  # Wait up to 15 seconds for locks to clear
}
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.String(255))
    def __repr__(self):
        return '<Post %r>' % self.title

class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'content')
        model = Post

post_schema = PostSchema()
posts_schema = PostSchema(many=True)

class ExecuteQuery(Resource):
    def post(self):
        query = request.get_json()['query']


        with db.engine.begin() as connection:
            connection.execute(text(query))
        return {"message": "Query executed successfully."}

class PostListResource(Resource):
    def get(self):
        posts = Post.query.all()
        return posts_schema.dump(posts)
    def post(self):
        new_post = Post(
            title=request.json['title'],
            content=request.json['content']
        )
        db.session.add(new_post)
        db.session.commit()
        return post_schema.dump(new_post)

class PostResource(Resource):
    def get(self, post_id):
        post = Post.query.get_or_404(post_id)
        return post_schema.dump(post)
    def patch(self, post_id):
        post = Post.query.get_or_404(post_id)
        if "title" in request.json:
            post.title = request.json['title']
        if "content" in request.json:
            post.content = request.json['content']
        db.session.commit()
        return post_schema.dump(post)
    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        return "This post has been deleted.", 204

api.add_resource(PostResource, '/posts/<int:post_id>')
api.add_resource(PostListResource, '/posts')
api.add_resource(ExecuteQuery, '/execute')
@app.route('/')
def index():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()