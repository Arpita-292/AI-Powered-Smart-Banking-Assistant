import os
import shutil
import tempfile
import unittest

import db_utils


class AadhaarLoginTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='siri_bank_test_')
        self.db_path = os.path.join(self.temp_dir, 'siri_bank.db')
        db_utils.DB_NAME = self.db_path
        db_utils.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_new_user_and_login_with_aadhaar(self):
        success, message = db_utils.create_new_user(
            full_name='New Customer',
            phone='9999999999',
            initial_deposit=2500,
            aadhaar_number='998877665544',
            password='MySecure@123'
        )

        self.assertTrue(success, message)
        user, auth_message = db_utils.authenticate_user('998877665544', 'MySecure@123')
        self.assertIsNotNone(user, auth_message)
        self.assertEqual(user['full_name'], 'New Customer')
        self.assertNotEqual(user.get('password_hash'), 'MySecure@123')


if __name__ == '__main__':
    unittest.main()
