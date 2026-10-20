import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
from build import ROOT, render, validate_registry

REGISTRY = ROOT / "apps.json"


class Scanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.script_count = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                raise AssertionError(f"duplicate HTML id: {a['id']}")
            self.ids.add(a["id"])
        if tag == "script":
            self.script_count += 1
        if tag == "a":
            self.links.append(a.get("href", ""))


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_registry_valid_and_all_apps_have_distinct_anchors(self):
        validate_registry(self.data)
        page = render(self.data)
        scan = Scanner()
        scan.feed(page)
        self.assertEqual(scan.script_count, 0)
        for app in self.data["apps"]:
            self.assertIn("app-" + app["id"], scan.ids)
        self.assertTrue(all(x.startswith(("https://", "mailto:")) for x in scan.links))

    def test_output_matches_registry(self):
        expected = render(self.data)
        self.assertEqual((ROOT / "index.html").read_text(encoding="utf-8"), expected)

    def test_refuses_duplicate_or_incomplete_apps(self):
        self.data["apps"].append(self.data["apps"][0])
        with self.assertRaisesRegex(ValueError, "duplicate app id"):
            validate_registry(self.data)
        self.data["apps"].pop()
        del self.data["apps"][0]["saveJa"]
        with self.assertRaisesRegex(ValueError, "invalid field saveJa"):
            validate_registry(self.data)

    def test_app_text_is_html_escaped(self):
        self.data["apps"][0]["name"] = '<script>alert("injected")</script>'
        text = render(self.data)
        self.assertNotIn('<script>alert("injected")</script>', text)
        self.assertIn("&lt;script&gt;", text)

    def test_existing_app_ads_authorization_preserved(self):
        text = (ROOT / "app-ads.txt").read_text(encoding="utf-8")
        self.assertEqual(text.strip(), "google.com, pub-2233916147865641, DIRECT, f08c47fec0942fa0")

    def test_support_email_consistent(self):
        page = render(self.data)
        self.assertIn("mailto:" + self.data["contactEmail"], page)
        self.assertEqual(page.count(self.data["privacyPolicyUrl"]), len(self.data["apps"]) + 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
