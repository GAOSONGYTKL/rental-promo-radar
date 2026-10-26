# 2026-10-26 单程费用核验
新页 cheapest one way car rental：只讲单程费与最终总价，不重写既有under25路线资格。
Avis原文：“Most locations do not charge a drop-off or one-way fee.”；其后明确地点有别，第三步核费用。官方URL见表，robots允许，命令行正文200保存在avis.html。
Enterprise原文：drop charge随地点/季节变，有则预订时披露。官方URL见表，网页工具读取正文与robots成功（通配禁止账户与reserve路径，不禁止本页）；命令行robots403已记，未重试绕过。
正文不写未取得的具体费率，不把缺字段当0。CSV金额空白，公式是编辑比较法不是官方报价。
素材：research/material-queue-20261025/queue.md的单程原话单例可用，保留英文，出处r/assholedesign日本经历，只作结账场景不外推美国费率。
对标：CarRentalSavers单程页已明确总价含单程费、路线差异及优惠，不能声称这些都没讲。MouseSavers已读租车入口及用车地点建议；RetailMeNot不再访问，不参与缺口。本文增量是逐次报价留档、缺项状态与差额对账的CSV，不是“别人都没讲总价”。未完成MouseSavers每站十页，未报30页。
设计：新页表格360px改纵向卡片；独立CSS可直接撤回。旧单程页只补原创图及通往新费用页的图链，不重写结论和数据。
明天：car rental without credit card；沿库存先核发卡机构/实体卡与柜台拒绝的区别，同一已覆盖取车资格并旧页。
