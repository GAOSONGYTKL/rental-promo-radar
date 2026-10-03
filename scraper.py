# ::ILANG
# [TYPE:code][ROLE:fetch_official_offers]
# ::BOUNDARY{never:绕反爬 编价格 编日期 使用登录凭据}
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib import request, robotparser
from urllib.parse import urlsplit, urljoin
from config import ROOT, load_config, slug

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.lines=[]; self.current=[]; self.hidden=0
    def flush(self):
        s=' '.join(''.join(self.current).split())
        if s: self.lines.append(s)
        self.current=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript','del','s'): self.hidden+=1
        if tag in ('p','div','h1','h2','h3','h4','h5','li','br'): self.flush()
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript','del','s'): self.hidden=max(0,self.hidden-1)
        if tag in ('p','div','h1','h2','h3','h4','h5','li'): self.flush()
    def handle_data(self, data):
        if not self.hidden: self.current.append(data)

def get(url, config):
    req=request.Request(url,headers={'User-Agent':config['user_agent'], 'Accept':'text/html,text/plain;q=0.8'})
    with request.urlopen(req, timeout=int(config['timeout_seconds'])) as response:
        if response.status != 200: raise ValueError('HTTP '+str(response.status))
        content=response.read(3_000_001)
        if len(content)>3_000_000: raise ValueError('Response exceeded size limit')
        return content.decode(response.headers.get_content_charset() or 'utf-8', errors='replace'), response.geturl()

def permitted(url, config):
    parts=urlsplit(url); robots_url=parts.scheme+'://'+parts.netloc+'/robots.txt'
    try:
        text,_=get(robots_url,config)
    except Exception as exc:
        # Fail closed when robots cannot be fetched; never guess permission.
        return False, 'robots unavailable: '+type(exc).__name__
    robots=robotparser.RobotFileParser(); robots.parse(text.splitlines())
    return robots.can_fetch(config['user_agent'],url), 'robots.txt checked'

def extract(lines, adapter, currency):
    text='\n'.join(lines); found=[]
    if adapter=='hertz_monthly':
        pattern=r'From R\s*([\d,]+) per month\s+Group ([^\n]+)\s+([^\n]+)'
        for price, group, model in re.findall(pattern,text):
            if len(model)<100 and ('Suzuki' in model or 'Toyota' in model or 'Volkswagen' in model or 'BMW' in model or 'Mercedes' in model):
                found.append(dict(plan=model+' / '+group,price=price.replace(',',''),currency=currency,period='month'))
    elif adapter=='cars2go':
        pattern=r'(Car Rentals at Corfu (?:Airport|Port)|Weekly Car Rentals|3-Day Car Rentals)\s+From\s+€([\d.]+)/(day|week)'
        for plan,price,period in re.findall(pattern,text):
            found.append(dict(plan=plan,price=price,currency=currency,period=period))
    elif adapter=='supreme_fleet':
        pattern=r'((?:BMW|Toyota|Renault|VW|Dacia|Skoda|Nissan) [^\n]{2,65})\s+from ([\d.]+)\s*€\s*/\s*day'
        for plan,price in re.findall(pattern,text):
            found.append(dict(plan=plan,price=price,currency=currency,period='day',conditions='Advertised starting rate applies to long-term rentals during the non-summer season.'))
    return found

def main():
    config=load_config(); now=datetime.now(timezone.utc).isoformat(); offers=[]; statuses=[]
    evidence=ROOT/'work/source-checks'; evidence.mkdir(parents=True,exist_ok=True)
    for provider in config['providers']:
        status=dict(provider=provider['name'],source_url=provider['source_url'],checked_at=now,status='unverified',detail='No approved extraction adapter for this page.')
        allowed,reason=permitted(provider['source_url'],config)
        if not allowed:
            status.update(status='blocked',detail=reason); statuses.append(status); continue
        try:
            raw,final_url=get(provider['source_url'],config)
            if urlsplit(final_url).netloc != urlsplit(provider['source_url']).netloc:
                raise ValueError('Cross-host redirect; requires manual source review')
            parser=VisibleText(); parser.feed(raw); parser.flush()
            (evidence/(slug(provider['name'])+'.txt')).write_text('\n'.join(parser.lines),encoding='utf-8')
            adapter,currency=config['adapters'].get(provider['name'],('', ''))
            rows=extract(parser.lines,adapter,currency)
            seen=set()
            for row in rows:
                key=(row['plan'],row['currency'])
                if key in seen: continue
                seen.add(key)
                row.update(provider=provider['name'],title=provider['name']+' — '+row['plan'],offer_url=provider['source_url'],source_url=provider['source_url'],fetched_at=now,source_sha256=hashlib.sha256(raw.encode()).hexdigest(),availability='unknown',valid_until=None)
                row['id']=slug(provider['name'])+'-'+hashlib.sha256('|'.join(key).encode()).hexdigest()[:10]
                offers.append(row)
            status.update(status='checked',detail='Official page fetched; '+str(len(rows))+' matching advertised rates extracted. No booking availability check was made.')
        except Exception as exc:
            status.update(status='error',detail=type(exc).__name__+': '+str(exc)[:160])
        statuses.append(status); time.sleep(1)
    output=dict(fetched_at=now,offers=offers,providers=statuses)
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/offers.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'offers':len(offers),'sources':len(statuses),'status_counts':{s:sum(x['status']==s for x in statuses) for s in ('checked','blocked','error')}}))

if __name__=='__main__': main()
