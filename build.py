# ::ILANG
# [TYPE:code][ROLE:render_static_site]
# ::BOUNDARY{never:编造价格 日期 域名 可订状态}
import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from config import ROOT, load_config, slug

def esc(value): return html.escape(str(value),quote=True)

def generate(config_path=None, output=None, data_path=None):
    config=load_config(config_path); base=config['base_url'].rstrip('/')
    out=Path(output or ROOT/'site'); out.mkdir(parents=True,exist_ok=True)
    # Remove only generator-owned route directories, inside the chosen output folder.
    for directory in ('providers','deals'):
        target=out/directory
        if target.resolve().parent != out.resolve(): raise ValueError('Unsafe output directory')
        if target.exists(): shutil.rmtree(target)
    data=json.loads(Path(data_path or ROOT/'data/offers.json').read_text(encoding='utf-8'))
    provider_names={p['name'] for p in config['providers']}
    now=datetime.now(timezone.utc)
    offers=[]
    for row in data['offers']:
        if row['provider'] not in provider_names: continue
        deadline=row.get('valid_until')
        if deadline and datetime.fromisoformat(deadline.replace('Z','+00:00')).date()<now.date(): continue
        if not row.get('plan') or not row.get('currency') or not row.get('price'): continue
        if (now-datetime.fromisoformat(row['fetched_at'])).total_seconds()>48*3600: continue
        offers.append(row)
    checks={s['provider']:s for s in data['providers']}
    template=(ROOT/'templates/base.html').read_text(encoding='utf-8')
    paths=[]; month=now.strftime('%B %Y')
    def write(path, title, description, content, schema, kind, lastmod):
        canonical=base+path if base else ''
        if base:
            schema.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':base+'/'},{'@type':'ListItem','position':2,'name':title,'item':canonical}]} if path!='/' else {'@type':'WebSite','name':config['brand'],'url':base+'/'})
        ld=json.dumps({'@context':'https://schema.org','@graph':schema},ensure_ascii=False).replace('<','\\u003c')
        metadata=(f'<link rel="canonical" href="{esc(canonical)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{esc(base)}/assets/share.svg">' if base else '<meta name="robots" content="noindex">')
        body=Template(template).substitute(title=esc(title),description=esc(description),brand=esc(config['brand']),locale=esc(config['locale']),metadata=metadata,jsonld=ld,content=content,checked=esc(lastmod),tagline=esc(config['tagline']))
        body=Template((ROOT/'templates'/kind).read_text(encoding='utf-8')).substitute(page=body)
        destination=out/('index.html' if path=='/' else path.strip('/')+'/index.html')
        destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(body,encoding='utf-8')
        paths.append((path,lastmod))
    def url(row): return '/deals/'+row['id']+'/'
    def offer_schema(row):
        obj={'@type':'Offer','name':row['title'],'price':row['price'],'priceCurrency':row['currency'],'url':row['offer_url'],'description':f"Advertised starting price per {row['period']}. Booking availability and expiry date are not verified."}
        if row.get('valid_until'): obj['priceValidUntil']=row['valid_until']
        # Never infer InStock from a marketing page.
        return obj
    def cards(rows):
        if not rows: return '<div class="empty">'+esc(config['empty_provider_message'])+'</div>'
        return ''.join('<article class="card"><span class="eyebrow">'+esc(r['provider'])+'</span><h3><a href="'+url(r)+'">'+esc(r['plan'])+'</a></h3><p class="price">'+esc(r['currency'])+' '+esc(r['price'])+' <small>/ '+esc(r['period'])+' · from</small></p><p>Official advertised rate. Availability unconfirmed.</p><a class="textlink" href="'+url(r)+'">Read terms & source →</a></article>' for r in rows)
    def itemlist(rows):
        return {'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':base+url(r)} for i,r in enumerate(rows)]} if base else {'@type':'ItemList','numberOfItems':len(rows)}
    content='<section class="hero"><span class="eyebrow">OFFICIAL SOURCES · NO MADE-UP CODES</span><h1>Your next rental.<br>A clearer deal.</h1><p>Browse official advertised rental rates. See the region, original currency, source and the limits before you book.</p><a class="button" href="#offers">Explore advertised rates</a></section>'
    content+='<section id="offers"><div class="sectionhead"><h2>Latest source-backed rates</h2><a href="/compare/">Compare the details →</a></div><div class="grid">'+cards(offers)+'</div></section><section><h2>Rental providers</h2><div class="providers">'
    content+=''.join('<a href="/providers/'+slug(p['name'])+'/">'+esc(p['name'])+' <span>→</span></a>' for p in config['providers'])+'</div></section><section class="notice"><h2>Clear about what we know</h2><p>These are advertised starting rates, not live booking quotes. Dates, location, duration and driver eligibility may change the final price. No coupon is called “verified” without a booking test. Original currencies are preserved.</p><p>We do not currently earn commissions. Affiliate links will only be enabled after approval under the relevant program terms.</p></section>'
    write('/',config['brand']+' | Official rental rates · '+month,'Official rental rates with source links, original currencies and honest availability limits.',content,[itemlist(offers)],'index.html',data['fetched_at'])
    for p in config['providers']:
        rows=[r for r in offers if r['provider']==p['name']]; check=checks.get(p['name'],{})
        content='<section class="pageintro"><span class="eyebrow">RENTAL PROVIDER</span><h1>'+esc(p['name'])+'</h1><p>'+esc(check.get('detail','This source has not been fetched.'))+'</p><a class="button" href="'+esc(p['source_url'])+'">Visit official offers ↗</a></section><div class="grid">'+cards(rows)+'</div>'
        schema={'@type':'Service','name':p['name']+' car rental','provider':{'@type':'Organization','name':p['name'],'url':p['website']}}
        if rows: schema['offers']=[offer_schema(r) for r in rows]
        write('/providers/'+slug(p['name'])+'/',p['name']+' official rental offers · '+month,p['name']+' rental rates and official source status. No invented codes or prices.',content,[schema],'provider.html',check.get('checked_at',data['fetched_at']))
    for row in offers:
        p=next(p for p in config['providers'] if p['name']==row['provider']); affiliate=p['affiliate_url']
        destination=affiliate or row['offer_url']; rel='sponsored noopener' if affiliate else 'noopener'
        content='<section class="pageintro"><span class="eyebrow">'+esc(row['provider'])+'</span><h1>'+esc(row['plan'])+'</h1><p class="price">'+esc(row['currency'])+' '+esc(row['price'])+' <small>/ '+esc(row['period'])+' · advertised from</small></p><p>'+esc(row.get('conditions','Price depends on rental dates, location, duration and eligibility. Check the official terms.'))+'</p><p>Availability: unconfirmed. Expiry: '+esc(row.get('valid_until') or 'not stated / not extracted')+'.</p><p>Source checked: '+esc(row['fetched_at'])+'</p><a class="button" rel="'+rel+'" href="'+esc(destination)+'">See official rental offer ↗</a><p class="source">Source: <a href="'+esc(row['source_url'])+'">'+esc(row['source_url'])+'</a></p>'+( '<p>Affiliate link: we may earn a commission.</p>' if affiliate else '')+'</section>'
        write(url(row),row['title']+' · '+month,row['title']+': '+row['currency']+' '+row['price']+' per '+row['period']+', advertised starting rate; check official terms.',content,[{'@type':'Service','name':row['plan'],'provider':{'@type':'Organization','name':row['provider']},'offers':offer_schema(row)}],'deal.html',row['fetched_at'])
    compare='<section class="pageintro"><span class="eyebrow">COMPARE TERMS, NOT JUST NUMBERS</span><h1>Rental rate comparison</h1><p>Different regions, currencies and rental periods are not directly comparable. No exchange-rate conversion or “cheapest” ranking is made.</p></section><div class="tablewrap"><table><thead><tr><th>Provider / plan</th><th>Advertised rate</th><th>Limits</th></tr></thead><tbody>'
    compare+=''.join('<tr><td><a href="'+url(r)+'">'+esc(r['title'])+'</a></td><td>'+esc(r['currency'])+' '+esc(r['price'])+' / '+esc(r['period'])+'</td><td>'+esc(r.get('conditions','Dates, location and eligibility apply. Availability unknown.'))+'</td></tr>' for r in offers)+'</tbody></table></div>'
    write('/compare/','Rental rate comparison · '+month,'Compare source-backed rental rates and restrictions in their original currencies.',compare,[itemlist(offers)],'compare.html',data['fetched_at'])
    article_files=sorted((ROOT/'content').glob('*.json'))
    guides=[]
    for article_file in article_files:
        article=json.loads(article_file.read_text(encoding='utf-8'))
        route='/guides/'+article['slug']+'/'
        guides.append('<li><a href="'+route+'">'+esc(article['title'])+'</a></li>')
        article_body='<article class="guide"><span class="eyebrow">RENTAL PROMO RADAR EDITORIAL TEAM</span><h1>'+esc(article['title'])+'</h1><p class="answer">'+esc(article['answer'])+'</p><p>Source review: '+esc(article['reviewed'])+'. No booking test was performed.</p>'+article['html']+'</article>'
        write(route,article['title'],article['answer'],article_body,[{'@type':'Article','headline':article['title'],'datePublished':article['reviewed'],'author':{'@type':'Organization','name':config['brand']+' Editorial Team'}}],'index.html',article['reviewed'])
    if guides:
        write('/guides/','Car rental coupon codes: practical guides','Source-backed rental coupon guides and original booking checklists.','<section class="pageintro"><h1>Car rental coupon codes: practical guides</h1><ul>'+''.join(guides)+'</ul></section>',[{'@type':'CollectionPage','name':'Rental coupon guides'}],'index.html',now.isoformat())
    information={
        'about':('About Rental Promo Radar','<p>Rental Promo Radar is an independent directory of publicly advertised car rental rates and offers. We link to official sources and preserve their original currencies and rental periods.</p><p>Our editorial team distinguishes advertised starting rates from live booking quotes. Availability, driver eligibility and booking terms must be checked with the rental provider. We do not invent coupon codes or prices.</p><p>Published by the Rental Promo Radar editorial team.</p>'),
        'privacy':('Privacy and disclosures','<p>This website is hosted on Cloudflare Pages. Requests are handled by Cloudflare, which may process IP addresses and technical request information to deliver and protect the site. We currently provide no account registration or contact form, and do not add advertising or analytics scripts in this version.</p><p>We plan to display third-party advertisements. When enabled, advertising providers may use cookies or similar technologies to process information about visits and ad interactions. Provider details and any required consent controls will be published before those integrations are enabled.</p><p>Affiliate links appearing on this site may generate a commission for Rental Promo Radar when a qualifying purchase is made. Such links will be disclosed and marked as sponsored. No affiliate commission is currently earned by this version.</p><p>Official rental providers and other linked websites have their own privacy policies. If you email us, your email address and message are used to respond to your request. Contact: <a href="mailto:contact@rentaldealradar.com">contact@rentaldealradar.com</a>.</p>'),
        'contact':('Contact Rental Promo Radar','<p>For source corrections, outdated rates, privacy questions or partnership enquiries, email the Rental Promo Radar editorial team.</p><p><a href="mailto:contact@rentaldealradar.com">contact@rentaldealradar.com</a></p><p>Please include the relevant page URL and official source when reporting a rate correction. Rental bookings, cancellations and refunds must be handled directly with the rental provider. Do not send passwords, payment card details or API keys.</p>')
    }
    for route,(title,body) in information.items():
        write('/'+route+'/',title,title+' for Rental Promo Radar.','<section class="pageintro"><h1>'+esc(title)+'</h1>'+body+'</section>',[{'@type':'WebPage','name':title}],'index.html',now.isoformat())
    (out/'404.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>Page not found | Rental Promo Radar</title><link rel="stylesheet" href="/assets/style.css"></head><body><main><section class="pageintro"><h1>404 — Page not found</h1><p>This address does not exist.</p><a href="/">Return to Rental Promo Radar</a></section></main></body></html>',encoding='utf-8')
    shutil.copytree(ROOT/'assets',out/'assets',dirs_exist_ok=True)
    public_data=dict(data); public_data['offers']=offers
    (out/'data').mkdir(exist_ok=True); (out/'data/offers.json').write_text(json.dumps(public_data,ensure_ascii=False,indent=2),encoding='utf-8')
    sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    if base:
        for path,lastmod in paths:
            node=ET.SubElement(sitemap,'url'); ET.SubElement(node,'loc').text=base+path; ET.SubElement(node,'lastmod').text=lastmod
    ET.ElementTree(sitemap).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (out/'robots.txt').write_text('User-agent: *\n'+('Allow: /\nSitemap: '+base+'/sitemap.xml\n' if base else 'Disallow: /\n'),encoding='utf-8')
    if base:
        worker='export default { async fetch(request, env) { const url = new URL(request.url); const target = new URL('+json.dumps(base)+'); if (url.hostname.endsWith(".pages.dev")) { url.protocol = target.protocol; url.host = target.host; return Response.redirect(url.toString(), 301); } return env.ASSETS.fetch(request); } };\n'
        (out/'_worker.js').write_text(worker,encoding='utf-8')
    (out/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: default-src \'self\'; style-src \'self\'; script-src \'none\'; img-src \'self\' data:; base-uri \'none\'; frame-ancestors \'none\'\n',encoding='utf-8')
    return {'pages':len(paths),'deals':len(offers),'base_url':base or 'NOT DEPLOYED'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--config'); parser.add_argument('--output'); args=parser.parse_args()
    print(json.dumps(generate(args.config,args.output)))
