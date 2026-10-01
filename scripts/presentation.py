"""Display-only language and evidence scopes; never promotes stored metadata flags."""
FORMAL_OVERLAY_STATES=frozenset({'verified_primary_metadata','official_publication_metadata_verified','published'})
TRANSLATIONS={
 'Unified legged-manipulator controller':'腿式移动操作机器人的统一控制器',
 'Coordinated Motion':'协调运动',
 'Conference/preprint year 2022; official PMLR citation year 2023. Legacy maniploco.github.io link returned empty content; working author project is manipulation-locomotion.github.io. No publication DOI is listed by PMLR.':'会议／首次预印本年份为 2022；PMLR 正式引用年份为 2023。核验时旧项目链接 maniploco.github.io 返回空内容，可用的作者项目地址为 manipulation-locomotion.github.io。PMLR 出版记录未列出出版 DOI。',
 '已发现官方实现仓库，但未运行代码或独立复现。 Author-linked reference PyTorch implementation; repository has legged_gym, rsl_rl and widowGo1 directories.':'已发现官方实现仓库，但未运行代码或独立复现。作者链接的参考实现使用 PyTorch，仓库包含 legged_gym、rsl_rl 和 widowGo1 目录。',
}
EDITION_LABELS={
 'version_of_record':'正式出版版本',
 'official_EMNLP_proceedings':'EMNLP 正式会议论文集版本',
 'official_ICCV_proceedings':'ICCV 正式会议论文集版本',
 'official_ECCV_ECVA_open_access':'ECCV／ECVA 官方开放获取版本',
 'official_CVPR_proceedings':'CVPR 正式会议论文集版本',
 'official_conference_proceedings':'正式会议论文集版本',
 'official_NeurIPS_Datasets_and_Benchmarks_proceedings':'NeurIPS 数据集与基准测试正式论文集版本',
 'formal_publication_verified_open_pdf_fallback_arxiv_v1':'已核验正式出版；开放 PDF 使用 arXiv v1 替代版本',
 'formal_publication_verified_open_pdf_fallback_arxiv_v4':'已核验正式出版；开放 PDF 使用 arXiv v4 替代版本',
 'arxiv_v2':'arXiv v2 预印本',
}
EVIDENCE_LABELS={'official_abstract':'官方摘要','official_project':'官方项目说明','official_paper':'正式论文','high':'高','medium':'中','low':'低'}

def translate(text):return TRANSLATIONS.get(text,text)
def edition_label(value):return EDITION_LABELS.get(value,value) if value else '尚未核验'
def evidence_label(value):return EVIDENCE_LABELS.get(value,value)

def overlay_status(paper):
    overlay=paper.get('verified_overlay') or {}
    if not (overlay.get('title') and overlay.get('authors')):return None
    state=paper.get('publication_status')
    if state in FORMAL_OVERLAY_STATES and overlay.get('publication_year'):
        return '正式书目已核验（独立补充）'
    if state=='preprint_metadata_verified_publication_unresolved':
        return '预印本书目已核验（正式出版未确认）'
    return None

def metadata_label(paper):
    return overlay_status(paper) or ('来源已核验' if paper.get('citation_verified') else '原始书目待核验')

def doi_label(paper):
    if paper.get('doi'):return paper['doi']
    # Null is not evidence of absence. Require the existing, explicit source note.
    note='No publication DOI is listed by PMLR.'
    documented=any(note in x for x in paper.get('notes',[]) if isinstance(x,str))
    source=any(x.startswith('https://proceedings.mlr.press/') for x in paper.get('sources',[]) if isinstance(x,str))
    return 'PMLR 出版记录未列出 DOI（据已保存来源备注）' if documented and source else '尚未核验'

def pdf_note_heading(paper):
    date=paper.get('verified_at') or '未注明日期'
    return f'以下是 {date} 的书目／链接核验记录；后续阅读范围见各阶段报告。'
