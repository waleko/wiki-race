from django.test import RequestFactory, TestCase

# Create your tests here.
from wiki_parser.views import parse_wiki_page


class ParserTests(TestCase):
    def test_simple_parsing(self):
        request = RequestFactory().get("/")
        response = parse_wiki_page(request, "London")

        self.assertEqual(response.status_code, 200)
        self.assertIn("London", response.content.__str__())
