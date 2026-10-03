# ::ILANG
# [TYPE:code][ROLE:parse_config]
# ::BOUNDARY{never:另存硬编码厂商清单}
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def load_config(path=None):
    text = Path(path or ROOT / '.ilang/site.ilang').read_text(encoding='utf-8')
    section, config = '', {'providers': [], 'adapters': {}}
    for raw in text.splitlines():
        line = raw.strip()
        match = re.match(r'::MODULE\{([^|}]+)', line)
        if match:
            section = match.group(1)
            continue
        if line.startswith('::') or not line or line.startswith('['):
            continue
        if section in ('SETTINGS', 'RENDER') and '=' in line:
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
        elif section == 'PROVIDERS' and '|' in line:
            parts = [x.strip() for x in line.split('|')]
            if len(parts) != 4:
                raise ValueError('Provider must have four columns')
            name, website, source, affiliate = parts
            for url in (website, source, affiliate):
                if url and not url.startswith('https://'):
                    raise ValueError('Only HTTPS sources and destinations are supported')
            config['providers'].append(dict(name=name, website=website, source_url=source, affiliate_url=affiliate))
        elif section == 'EXTRACTION' and '|' in line:
            name, adapter, currency = [x.strip() for x in line.split('|')]
            config['adapters'][name] = (adapter, currency)
    site = re.search(r'::STATE\{@SITE, brand:([^,]+), niche:([^,]+), domain:([^}]+)', text)
    if not site:
        raise ValueError('Missing @SITE declaration')
    config.update(zip(('brand', 'niche', 'domain'), (x.strip() for x in site.groups())))
    if config.get('base_url') and not config['base_url'].startswith('https://'):
        raise ValueError('Production base_url must be HTTPS')
    return config

def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
