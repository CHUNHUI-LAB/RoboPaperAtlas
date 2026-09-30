'use strict';
// KaTeX runs only at build time. Browser output is static HTML+MathML with local fonts.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),katex=require('katex');
if(katex.version!=='0.18.9')throw new Error('Pinned KaTeX version required');
const input=path.join(root,'data/reader-math.json'),raw=fs.readFileSync(input),data=JSON.parse(raw);
if(data.schema_version!==1||data.paper_id!=='rpa-0062'||data.report!=='stage3'||!Array.isArray(data.entries)||data.entries.length>100)throw new Error('Unexpected math scope');
const rendered={};
for(const e of data.entries){
 if(!/^[a-zA-Z][a-zA-Z0-9-]*$/.test(e.id)||e.id in rendered||typeof e.latex!=='string'||e.latex.length>4000||typeof e.display_mode!=='boolean')throw new Error('Unsafe math entry');
 if(/\\(?:href|url|includegraphics|html\w*|def|gdef|newcommand|renewcommand)\b/.test(e.latex))throw new Error('Math resource/macro commands are not permitted');
 rendered[e.id]=katex.renderToString(e.latex,{displayMode:e.display_mode,output:'htmlAndMathml',throwOnError:true,strict:'error',trust:false,maxSize:20,maxExpand:1000});
 if(/katex-error|<script|javascript:|<iframe/i.test(rendered[e.id]))throw new Error('Unsafe math output');
}
const vendor=path.join(root,'assets/vendor/katex'),fonts=path.join(vendor,'fonts'),distribution=path.join(root,'node_modules/katex/dist');
fs.mkdirSync(fonts,{recursive:true});
// Keep only modern WOFF2 references, avoiding browser calls to package registries/CDNs.
let css=fs.readFileSync(path.join(distribution,'katex.min.css'),'utf8').replace(/,url\(fonts\/[^)]+\.(?:woff|ttf)\) format\("(?:woff|truetype)"\)/g,'');
if(/https?:|\.ttf|\.woff\)/.test(css))throw new Error('Unexpected remote or legacy font reference');
for(const match of css.matchAll(/url\(fonts\/([^/)]+\.woff2)\)/g))fs.copyFileSync(path.join(distribution,'fonts',match[1]),path.join(fonts,match[1]));
fs.writeFileSync(path.join(vendor,'katex.min.css'),css);fs.copyFileSync(path.join(root,'node_modules/katex/LICENSE'),path.join(vendor,'LICENSE.txt'));
fs.copyFileSync(path.join(root,'docs/katex-font-notices.txt'),path.join(vendor,'FONT-NOTICES.txt'));fs.copyFileSync(path.join(root,'docs/katex-font-license.txt'),path.join(vendor,'OFL.txt'));
const result={schema_version:1,katex_version:katex.version,input_sha256:crypto.createHash('sha256').update(raw).digest('hex'),rendered};
fs.writeFileSync(path.join(root,'data/reader-math-rendered.json'),JSON.stringify(result)+'\n');
console.log('Prepared '+Object.keys(rendered).length+' strict KaTeX expressions, static MathML/HTML and local WOFF2 fonts');
