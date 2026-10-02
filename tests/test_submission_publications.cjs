'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),data=JSON.parse(fs.readFileSync(path.join(root,'submit-preview/data/venues.json'),'utf8'));
function setup(){
 const nodes={};function get(id){if(!nodes[id])nodes[id]={value:'',textContent:'',_html:'',options:[],classList:{remove(){}},add(o){this.options.push(o)},set innerHTML(v){this._html=v;if(v.startsWith('<option')){this.options=[{value:''}];this.value=''}},get innerHTML(){return this._html}};return nodes[id]}
 const ctx=vm.createContext({document:{getElementById:get,querySelectorAll:()=>[]},URL,URLSearchParams,Option:function(text,value){this.text=text;this.value=value},location:{hash:''},history:{replaceState(){}},console});
 const src=fs.readFileSync(path.join(root,'submit-preview/app.js'),'utf8').split("const sourceURL=")[0];vm.runInContext(src,ctx);ctx.fixture=data;vm.runInContext('data=fixture',ctx);get('p-yearmode').value='publication_year';return {ctx,get,run:s=>vm.runInContext(s,ctx)};
}
test('same-publication venue, year, forum, status and topic intersection',()=>{const {ctx,run}=setup();ctx.p=data.publications.find(p=>p.paper_id==='rpa-0052');assert.equal(run("matchesPublication(p,{venue:'ral',yearmode:'publication_year',year:'2025',forum:'journal',status:'published',topic:'wbc'})"),true);assert.equal(run("matchesPublication(p,{venue:'icra',forum:'workshop'})"),false);assert.equal(run("matchesPublication(p,{yearmode:'edition_year',year:'2025'})"),false);ctx.p=data.publications.find(p=>p.paper_id==='rpa-0012');assert.equal(run("matchesPublication(p,{yearmode:'edition_year',year:'2022',forum:'main_conference'})"),true);assert.equal(run("matchesPublication(p,{yearmode:'publication_year',year:'2023'})"),true);assert.equal(run("matchesPublication(p,{yearmode:'publication_year',year:'2022'})"),false)});
test('derived counts and journal rendering do not fabricate conference editions',()=>{const {get,run}=setup();run('renderPapers()');assert.match(get('paper-count').textContent,/8 篇匹配.*8 篇/);assert.match(get('migration-notice').textContent,/8 篇.*95.*87/);assert.match(get('paper-list').innerHTML,/IEEE RA-L · 期刊/);assert.match(get('paper-list').innerHTML,/AAAI · 主会/);assert.doesNotMatch(get('paper-list').innerHTML,/届次 null/);get('p-forum').value='journal';run('renderPapers()');assert.match(get('paper-count').textContent,/1 篇匹配/);assert.doesNotMatch(get('paper-list').innerHTML,/会议届次与出版年份不同/);get('p-forum').value='workshop';run('renderPapers()');assert.match(get('paper-count').textContent,/0 篇匹配/)});
test('year choices follow selected semantic mode and preserve valid selections',()=>{const {get,run}=setup();run('refreshYears()');assert.deepEqual(get('p-year').options.map(x=>x.value),['','2023','2024','2025','2026']);get('p-year').value='2023';get('p-yearmode').value='edition_year';run('refreshYears()');assert.equal(get('p-year').value,'');assert.deepEqual(get('p-year').options.map(x=>x.value),['','2022','2024','2025','2026']);get('p-year').value='2025';get('p-yearmode').value='publication_year';run('refreshYears()');assert.equal(get('p-year').value,'2025')});
test('historical identity never becomes a sixteenth recommendation or policy snapshot',()=>{const {get,run}=setup();run('renderList()');assert.equal(get('venue-count').textContent,'15 个渠道 · 摘要来自官方资料');assert.doesNotMatch(get('venue-list').innerHTML,/AAAI/);assert.equal(run("latest(data.venues.find(v=>v.id==='ral')).kind"),'journal_policy_snapshot');run("openVenue('aaai')");assert.match(get('detail').innerHTML,/渠道不存在/) });

test('experience types and links stay source-specific across venues',()=>{
 const {run}=setup();
 const icra=run("renderExperiences('icra')");
 assert.match(icra,/3 条已读来源/);
 assert.match(icra,/作者建议 · 非会议规范/);
 assert.match(icra,/匿名网友自述 · 未独立认证/);
 assert.match(icra,/Seita’s Place/);
 assert.match(icra,/未观看视频/);
 assert.match(icra,/页面仅显示约 3 个月前；绝对日期未核定/);
 assert.doesNotMatch(icra,/查看知乎原文|RA-L 官方说明|3 条历史亲历|null 年/);
 const cvpr=run("renderExperiences('cvpr')");
 assert.match(cvpr,/1 条已读来源/);
 assert.match(cvpr,/Devi Parikh、Dhruv Batra、Stefan Lee/);
 assert.doesNotMatch(cvpr,/RA-L 官方说明|作者自报 · 非独立认证|2027 页数/);
 const ral=run("renderExperiences('ral')");
 assert.match(ral,/4 条已读来源/);
 assert.match(ral,/RA-L 官方说明/);
 for(const record of data.experiences.records.filter(r=>r.source_type==='first_person_self_report'))assert.match(ral,new RegExp(record.id));
});
test('official conflict and editorial synthesis are explicitly separate from anecdotes',()=>{
 const {run}=setup(),html=run("renderExperiences('icra')");
 assert.match(html,/aria-label="官方规则核对"/);
 assert.match(html,/完整论文最多 8 页，包含参考文献/);
 assert.match(html,/2025-03-06.*6\+n/);
 assert.match(html,/终稿冲突尚未解决/);
 assert.match(html,/aria-label="编辑归纳"/);
 assert.match(html,/不是原作者共同结论或官方要求/);
 assert.match(html,/不把这段旧内容认定为 2027 终稿要求/);
 assert.doesNotMatch(run("renderExperiences('iros')"),/aria-label="官方规则核对"/);
});
test('empty and unrelated venues never borrow an RA-L label or source',()=>{
 const {run}=setup(),html=run("renderExperiences('jfr')");
 assert.match(html,/暂无已核读的公开来源/);
 assert.doesNotMatch(html,/RA-L|知乎|历史亲历/);
});
test('cross-venue relevance does not duplicate the underlying source records',()=>{
 const {run}=setup();
 assert.equal(data.experiences.records.length,7);
 assert.equal(new Set(data.experiences.records.map(r=>r.id)).size,7);
 assert.equal(run("experienceMatches(data.experiences.records.find(r=>r.id==='milford-robotics-paper-structure-2023'),'iros')"),true);
 assert.equal(run("experienceMatches(data.experiences.records.find(r=>r.id==='parikh-batra-lee-rebuttals-2020'),'ral')"),false);
});
test('new experience and rule fields escape markup and reject unsafe source URLs',()=>{
 const {ctx,run}=setup();
 ctx.fixture=JSON.parse(JSON.stringify(data));run('data=fixture');
 const record=ctx.fixture.experiences.records.find(r=>r.id==='milford-robotics-paper-structure-2023');
 record.source_label='<img src=x onerror=alert(1)>';record.source_url='javascript:alert(1)';record.source_author='<svg onload=alert(1)>';
 ctx.fixture.experiences.official_checks[0].title='<img src=x>';
 const html=run("renderExperiences('icra')");
 assert.doesNotMatch(html,/<img|<svg|href="javascript:/);
 assert.match(html,/&lt;img/);assert.match(html,/&lt;svg/);
});

test('venue overview exposes source-backed summaries before any selection',()=>{
 const {get,run}=setup();run('renderList()');
 assert.equal((get('venue-list').innerHTML.match(/class="venue-card"/g)||[]).length,15);
 assert.match(get('venue-list').innerHTML,/研究|机器人/);assert.match(get('venue-list').innerHTML,/投稿形式/);assert.match(get('venue-list').innerHTML,/时间概况/);
 assert.match(get('venue-list').innerHTML,/两阶段评审 · 扩展摘要后按邀请提交全文/);
 assert.match(get('venue-list').innerHTML,/暂无可核验日期/);
 get('query').value='实地验证';run('renderList()');assert.equal(get('venue-count').textContent,'1 个渠道 / 共 15 个 · 摘要来自官方资料');assert.match(get('venue-list').innerHTML,/Journal of Field Robotics/);
 get('query').value='不可能匹配的词';run('renderList()');assert.equal(get('venue-count').textContent,'0 个渠道 / 共 15 个 · 摘要来自官方资料');assert.match(get('venue-list').innerHTML,/重置筛选/);
});
test('global experiences show all unique summaries and provenance, with honest empty states',()=>{
 const {get,run}=setup();run('renderExperienceOverview()');
 assert.equal((get('experience-list').innerHTML.match(/data-experience-id=/g)||[]).length,7);
 assert.equal((get('experience-synthesis').innerHTML.match(/class="synthesis-card"/g)||[]).length,3);
 assert.match(get('experience-synthesis').innerHTML,/不是原作者共同结论或官方要求/);
 for(const r of data.experiences.records)assert.ok(get('experience-list').innerHTML.includes(r.body_summary));
 get('e-venue').value='icra';run('renderExperienceOverview()');assert.match(get('experience-count').textContent,/3 条已读来源/);assert.match(get('experience-checks').innerHTML,/终稿冲突尚未解决/);
 get('e-type').value='author_advice';run('renderExperienceOverview()');assert.match(get('experience-count').textContent,/1 条已读来源/);
 get('e-venue').value='jfr';run('renderExperienceOverview()');assert.match(get('experience-count').textContent,/0 条已读来源/);assert.match(get('experience-list').innerHTML,/没有收录不代表没有相关经验/);
});
test('deadline overview separates initial, conditional, historical and disputed information',()=>{
 const {get,run}=setup();run('renderDeadlines()');const html=get('deadline-list').innerHTML,first=html.split('常规期刊、待确认与历史届次')[0];
 assert.match(first,/3 个已核验节点/);assert.match(first,/2026-11-10/);assert.match(first,/2026-11-16/);assert.match(first,/2026-12-04/);
 assert.doesNotMatch(first,/2027-04-16|2026-10-12|2026-09-16/);
 assert.match(html,/仅适用于已完成前置阶段并获邀请的作者/);assert.match(html,/日期存在冲突/);assert.match(html,/本届官网来源待确认/);assert.match(html,/全年接收投稿/);
 get('d-venue').value='icra';run('renderDeadlines()');assert.match(get('deadline-list').innerHTML,/0 个已核验节点/);assert.match(get('deadline-list').innerHTML,/暂不作可操作截止日/);
 get('d-venue').value='rss';run('renderDeadlines()');assert.match(get('deadline-list').innerHTML,/1 个已核验节点/);
});
test('routes preserve encoded filters and detail return destination without arbitrary selection',()=>{
 const {ctx,get,run}=setup();
 assert.equal(run("parseRoute('#experiences?ev=ral&eq=%E4%BF%AE%E8%AE%A2').tab"),'experiences');assert.equal(run("parseRoute('#experiences?ev=ral&eq=%E4%BF%AE%E8%AE%A2').params.get('eq')"),'修订');
 assert.equal(run("parseRoute('#bad').tab"),'venues');
 get('query').value='感知';get('kind').value='journal';assert.match(run("venueHref('ral')"),/^#venues\/ral\?q=/);
 ctx.location={hash:'#venues/rss?from=deadlines&dv=rss&edition=rss-2027'};assert.equal(run('returnHref()'),'#deadlines?dv=rss');
 ctx.location={hash:'#venues/ral?q=test&kind=journal&edition=ral-policy-20261001'};assert.equal(run('returnHref()'),'#venues?q=test&kind=journal');
 const src=fs.readFileSync(path.join(root,'submit-preview/app.js'),'utf8');assert.doesNotMatch(src,/if\(!selected\)openVenue\('rss'\)/);
 assert.match(src,/navigator\.clipboard\.writeText\(url\)/);assert.match(src,/id="copy-status".*role="status"/);assert.match(src,/addEventListener\('hashchange',route\)/);
});
