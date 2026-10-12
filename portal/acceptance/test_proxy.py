from ipaddress import ip_network

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from core.middleware import TrustedProxyMiddleware


@override_settings(TRUSTED_PROXY_NETWORKS=[ip_network("192.0.2.0/24")])
class ProxyAcceptance(SimpleTestCase):
    def apply(self, peer, source, proto="https"):
        request = RequestFactory().get("/", REMOTE_ADDR=peer, HTTP_X_FORWARDED_FOR=source, HTTP_X_FORWARDED_PROTO=proto)
        TrustedProxyMiddleware(lambda request: HttpResponse())(request)
        return request

    def test_untrusted_peer_cannot_spoof_address_or_https(self):
        request = self.apply("198.51.100.2", "203.0.113.5")
        self.assertEqual(request.META["REMOTE_ADDR"], "198.51.100.2")
        self.assertNotIn("HTTP_X_FORWARDED_PROTO", request.META)
        self.assertNotIn("HTTP_X_FORWARDED_FOR", request.META)

    def test_trusted_proxy_maps_single_client_address(self):
        request = self.apply("192.0.2.3", "203.0.113.5")
        self.assertEqual(request.META["REMOTE_ADDR"], "203.0.113.5")
        self.assertEqual(request.META["HTTP_X_FORWARDED_PROTO"], "https")

    def test_appended_or_malformed_addresses_are_not_trusted(self):
        for source in ["203.0.113.5, 198.51.100.2", "unknown", ""]:
            self.assertEqual(self.apply("192.0.2.3", source).META["REMOTE_ADDR"], "192.0.2.3")

    def test_ipv6_client_is_supported(self):
        self.assertEqual(self.apply("192.0.2.3", "2001:db8::5").META["REMOTE_ADDR"], "2001:db8::5")
