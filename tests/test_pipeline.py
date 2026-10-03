# ::ILANG
# [TYPE:code][ROLE:verify_pipeline]
# ::BOUNDARY{never:把测试样本当真实线上价格}
import json
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from config import ROOT, load_config
from scraper import extract
from build import generate

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'work').mkdir(exist_ok=True)

    def test_expired_and_stale_rates_removed_from_pages_and_public_data(self):
        data=json.loads((ROOT/'data/offers.json').read_text(encoding='utf-8'))
        now=datetime.now(timezone.utc)
        expired=dict(data['offers'][0],valid_until=(now-timedelta(days=1)).date().isoformat())
        stale=dict(data['offers'][0],fetched_at=(now-timedelta(hours=49)).isoformat())
        data['offers']=[expired,stale]
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as temp:
            folder=Path(temp); fixture=folder/'data.json'
            fixture.write_text(json.dumps(data),encoding='utf-8')
            result=generate(output=folder/'site',data_path=fixture)
            self.assertEqual(result['deals'],0)
            self.assertEqual(json.loads((folder/'site/data/offers.json').read_text())['offers'],[])

    def test_hertz_plan_not_price_paragraph(self):
        rows=extract(['From R 5,999 per month','Group A - MDMR','Suzuki Swift or similar'], 'hertz_monthly','ZAR')
        self.assertEqual(rows[0]['price'],'5999')
        self.assertEqual(rows[0]['plan'],'Suzuki Swift or similar / A - MDMR')
        self.assertEqual(extract(['save R 100','original price R 200'], 'hertz_monthly','ZAR'),[])

    def test_cars2go_plan_and_period(self):
        rows=extract(['Weekly Car Rentals','From','€89/week'], 'cars2go','EUR')
        self.assertEqual(rows[0]['period'],'week')

    def test_config_mutation_changes_site_and_urls(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as temp:
            path=Path(temp); config=(ROOT/'.ilang/site.ilang').read_text(encoding='utf-8')
            config=re.sub(r'^base_url\s*=.*$', 'base_url = https://example.test', config, flags=re.M)
            config=config.replace('Regal Rental |','Config Mutation Probe |')
            cp=path/'config.ilang'; cp.write_text(config,encoding='utf-8')
            output=path/'site'; result=generate(cp,output)
            self.assertTrue((output/'providers/config-mutation-probe/index.html').exists())
            self.assertFalse((output/'providers/regal-rental/index.html').exists())
            sitemap=ET.parse(output/'sitemap.xml')
            urls=sitemap.findall('{*}url/{*}loc')
            self.assertTrue(all(u.text.startswith('https://example.test/') for u in urls))
            deals=sum('/deals/' in u.text for u in urls)
            self.assertEqual(deals,result['deals'])
            self.assertIn('https://example.test/sitemap.xml',(output/'robots.txt').read_text())
            for page in output.rglob('*.html'):
                raw=page.read_text(encoding='utf-8')
                if page.name=='404.html':
                    self.assertIn('noindex',raw)
                    self.assertIn('Page not found',raw)
                    continue
                self.assertIn('rel="canonical"',raw)
                for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',raw):
                    schema=json.loads(block)
                    self.assertEqual(schema['@context'],'https://schema.org')
                    self.assertNotIn('InStock',block)

    def test_providers_read_from_config(self):
        c=load_config()
        self.assertEqual(len({p['name'] for p in c['providers']}),len(c['providers']))
        self.assertTrue(all(p['source_url'].startswith('https://') for p in c['providers']))

if __name__=='__main__': unittest.main()
