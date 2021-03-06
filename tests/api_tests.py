import unittest
import os
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse

os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session



class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

        Base.metadata.create_all(engine)

    def test_get_empty_posts(self):

        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data, [])

    def test_get_posts(self):
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just a test")

        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Still a test")

    def test_get_post(self):
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id), headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data.decode('ascii'))
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Still a test")

    def test_get_non_existent_post(self):
        response = self.client.get("/api/posts/1")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["message"], "Could not find post with id 1")

    def test_unsupported_accept_header(self):
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/xml")]
        )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["message"],
                         "Request must accept application/json data")


    def test_delete_post(self):
        post = models.Post(title="Example Post", body="Just a test")
        session.add_all([post])
        session.commit()

        response = self.client.get('/api/posts', headers=[("Accept", "application/json")])
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(1, len(data))

        response = self.client.post("/api/posts/1/delete", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        response = self.client.get('/api/posts', headers=[("Accept", "application/json")])
        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(0, len(data))

    def test_get_posts_with_title(self):
        postA = models.Post(title="Post with bells", body="Just a test")
        postB = models.Post(title="Post with whistles", body="Still a test")
        postC = models.Post(title="Post with bells and whistles",
                            body="Another test")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Another test")

    def test_get_posts_with_text(self):
        postA = models.Post(title="Post with bells", body="whistles")
        postB = models.Post(title="Post with whistles", body="bells")
        postC = models.Post(title="Post with bells and whistles",
                            body="bells and whistles")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles&body_like=bells",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "bells")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "bells and whistles")

    def test_post_post(self):
        data = {
            "title": "Example Post",
            "body": "Just a test"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")

    def test_update_post(self):
        data = {
            "title": "",
            "body": ""
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")

        data = {
            "title": "New Post Title",
            "body": "New Post Content"
        }

        response = self.client.put("/api/posts/1",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        #self.assertEqual(urlparse(response.headers.get("Location")).path,
                         #"/api/posts/1")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)
        self.assertEqual(response.mimetype, "application/json")

        #TODO If I try to check post content I am told post object does not accept indexing.
        post = posts[0]
        self.assertEqual(post.title, "New Post Title")
        self.assertEqual(post.body, "New Post Content")

    def test_unsupported_mimetype(self):
        data = "<xml></xml>"
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["message"],
                         "Request must contain application/json data")

    def test_invalid_data(self):
        data = {
            "title": "Example Post",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def test_missing_data(self):
        data = {
            "title": "Example Post",
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(data["message"], "'body' is a required property")

    def tearDown(self):
        session.close()
        Base.metadata.drop_all(engine)

if __name__ == "__main__":
    unittest.main()
