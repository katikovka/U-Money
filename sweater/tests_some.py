import os
import string
import unittest
from flask_testing import TestCase

from sweater.app import app, db, User, generate_secure_string


class TestApp(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['SECRET_KEY'] = os.environ["secret_key"]
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('about.html')

        # Test registration form submission
        response = self.client.post('/register', data={
            'login': 'test_user',
            'name': 'Test User',
            'password': 'password123',
            're_password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'Redirecting', response.data)

        # Check if the user is now registered
        user = User.query.filter_by(login='test_user').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Test User')

    def test_register_routes(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('register.html')

    def test_login_routes(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('login.html')

    def test_generate_secure_string(self):
        secure_string = generate_secure_string()
        self.assertEqual(len(secure_string), 50)

        custom_length = 20
        secure_string_custom = generate_secure_string(custom_length)
        self.assertEqual(len(secure_string_custom), custom_length)

        allowed_characters = string.ascii_letters
        for char in secure_string:
            self.assertIn(char, allowed_characters)

        secure_string_another = generate_secure_string()
        self.assertNotEqual(secure_string, secure_string_another)

    def test_about_route(self):
        response = self.client.get('/home')
        self.assertEqual(response.status_code, 302)

    def test_logout_route(self):
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)

    def test_contact_route(self):
        # Test the behavior of the contact route
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 302)

    def test_add_category_route(self):
        # Test the behavior of the add_category route
        response = self.client.post('/add_category', data={'categories': 'TestCategory1 TestCategory2'})
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()
