/* Yorisuguri Note GA4: page views and affiliate link clicks. */
(function () {
  'use strict';
  if (window.__yorisuguriAnalytics) return;
  window.__yorisuguriAnalytics = true;
  var id = 'G-CKLWHE528W';
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  var group = location.hostname.indexOf('beauty.') === 0 ? 'beauty' :
    location.pathname.indexOf('/cooking/') !== -1 ? 'cooking' :
    location.pathname.indexOf('/work/') !== -1 ? 'work' : 'general';
  var cleanUrl = location.origin + location.pathname;
  var referrer = '';
  try { if (document.referrer) { var ref = new URL(document.referrer); referrer = ref.origin + ref.pathname; } } catch (_) {}
  window.gtag('js', new Date());
  window.gtag('config', id, {
    content_group: group,
    page_location: cleanUrl,
    page_referrer: referrer,
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  });
  var tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
  document.head.appendChild(tag);
  document.addEventListener('click', function (event) {
    var link = event.target && event.target.closest ? event.target.closest('a[href]') : null;
    if (!link) return;
    var url;
    try { url = new URL(link.href, location.href); } catch (_) { return; }
    if (!/^(px\.a8\.net|www\.a8\.net|a8\.net)$/.test(url.hostname)) return;
    window.gtag('event', 'affiliate_click', {
      affiliate_network: 'a8',
      link_domain: url.hostname,
      article_path: location.pathname,
      content_group: group,
      transport_type: 'beacon'
    });
  });
})();
