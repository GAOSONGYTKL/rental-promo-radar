::ILANG
[TYPE:instructions][PROJECT:Rental Promo Radar][LANG:zh]
::OBJECTIVE{维护真实租车优惠目录 抓取和构建只能使用Python标准库}
::STATE{@CONFIG, source:.ilang/site.ilang, role:唯一厂商和渲染配置真源}
::RULE{允许:修改代码 模板 配置 测试 抓公开官方页面}
::RULE{发布:只使用用户授权的GitHub与Cloudflare 不创建收费资源}
::RULE{提取:厂商加方案加币种去重 不确定的价格日期丢弃}
::RULE{robots不可读或禁止⇒不抓该来源 不绕反爬}
::RULE{失败或48小时未更新⇒不展示旧价格}
::RULE{发布前⇒使用Cloudflare实际返回地址回写base_url和domain 验canonical sitemap robots}
::BOUNDARY{never:编价格 优惠 可订状态 佣金 登录信息 伪造收入 自动发布社交贴文|scope:permanent}
::BOUNDARY{never:把域名年龄 SEO权重或收入当保证|scope:permanent}
::CHECK{python -m unittest discover -s tests -v; python build.py}
