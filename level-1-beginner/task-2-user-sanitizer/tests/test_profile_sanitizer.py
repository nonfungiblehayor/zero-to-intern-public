import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from profile_sanitizer import sanitize_profile


class TestProfileSanitizer(unittest.TestCase):

    def test_already_clean_profile(self):
        """A profile that is already trimmed and formatted passes validation."""
        profile = {
            "username": "clean_user",
            "email": "user@domain.com",
            "full_name": "Clean User"
        }
        result = sanitize_profile(profile)
        self.assertEqual(result["username"], "clean_user")
        self.assertEqual(result["email"], "user@domain.com")
        self.assertEqual(result["full_name"], "Clean User")
        self.assertTrue(result["is_valid"])

    def test_bug_reproduction_whitespace_not_stripped(self):
        """
        REPRODUCTION TEST 1 (Ticket #AUTH-201):
        Leading and trailing whitespace must be stripped from all fields.
        Under the bug, string method returns are ignored, so spaces remain!
        """
        profile = {
            "username": "   dev_sam   ",
            "email": "sam@company.org   ",
            "full_name": "  Sam Taylor  "
        }
        result = sanitize_profile(profile)
        self.assertEqual(result["username"], "dev_sam", "Username whitespace was not stripped!")
        self.assertEqual(result["email"], "sam@company.org", "Email whitespace was not stripped!")
        self.assertEqual(result["full_name"], "Sam Taylor", "Full name whitespace was not stripped!")

    def test_bug_reproduction_casing_not_normalized(self):
        """
        REPRODUCTION TEST 2 (Ticket #AUTH-202):
        Email must be converted to lowercase, and full name converted to Title Case.
        Under the bug, strings remain unnormalized!
        """
        profile = {
            "username": "pat_lee",
            "email": "PAT.LEE@EXAMPLE.COM",
            "full_name": "pat lee"
        }
        result = sanitize_profile(profile)
        self.assertEqual(result["email"], "pat.lee@example.com", "Email was not converted to lowercase!")
        self.assertEqual(result["full_name"], "Pat Lee", "Full name was not converted to Title Case!")


if __name__ == "__main__":
    unittest.main()
