'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../dist/atlas-preview/index.html'),'utf8');
const source=html.match(/<script>([\s\S]*?)<\/script>/)[1],data=JSON.parse(html.match(/<script id="prototype-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const context={module:{exports:{}}};vm.runInNewContext(source,context);module.exports={source,data,css:html.match(/<style>([\s\S]*?)<\/style>/)[1],core:context.module.exports};
