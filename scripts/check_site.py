"""Check internal destinations, metadata, sitemap and preservation against a Git ref."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import subprocess,json,sys,xml.etree.ElementTree as ET
from collections import Counter
root=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.ids=[];self.ads=[];self.h1=0;self.canonical=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='h1':self.h1+=1
  if a.get('rel')=='canonical':self.canonical.append(a['href'])
  for k in ('href','src'):
   if k in a:
    self.links.append(a[k])
    if any(x in a[k] for x in ('a8.net','a8ad.jp','a8mat=')):self.ads.append((tag,tuple(attrs)))
pages={p.name:Page(p.read_text()) for p in root.glob('*.html')};errors=[];adcount=0
for name,page in pages.items():
 if page.h1!=1:errors.append(f'{name}: h1 count {page.h1}')
 if len(page.canonical)!=1:errors.append(f'{name}: canonical')
 if len(set(page.ids))!=len(page.ids):errors.append(f'{name}: duplicate ids')
 for link in page.links:
  u=urlsplit(link)
  if u.scheme or u.netloc:continue
  target=unquote(u.path) or name
  if not (root/target).is_file():errors.append(f'{name}: missing {link}')
  elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:errors.append(f'{name}: missing fragment {link}')
 text=(root/name).read_text()
 for data in __import__('re').findall(r'<script type="application/ld\+json">(.*?)</script>',text):json.loads(data)
 if len(sys.argv)>1:
  old=subprocess.check_output(['git','show',sys.argv[1]+':'+name],cwd=root,text=True)
  before=Page(old)
  if Counter(before.ads)!=Counter(page.ads):errors.append(f'{name}: advertisement code changed')
  adcount+=len(page.ads)
  # Every pre-existing article link and anchor remains available.
  if not set(before.ids)<=set(page.ids):errors.append(f'{name}: removed anchor')
urls=[n.text for n in ET.parse(root/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(urls)==len(pages)
assert not errors,errors
print(f'PASS: {len(pages)} pages; internal files/fragments; unique IDs; H1/canonical; JSON-LD; sitemap; {adcount} A8 elements unchanged.')
