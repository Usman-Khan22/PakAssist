import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawn } from 'node:child_process';

const base=process.env.TEST_BASE_URL || 'http://127.0.0.1:4176';
const server=process.env.TEST_BASE_URL ? null : spawn(process.execPath, ['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4176','--strictPort'], {windowsHide:true,stdio:'pipe'});
if(server) {
  await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(new Error('Test server did not start')),15000);
    server.on('error',reject);
    server.on('exit',code=>reject(new Error(`Test server exited: ${code}`)));
    server.stdout.on('data',data=>{if(data.toString().includes('Local:')){clearTimeout(timeout);resolve();}});
  }).catch(error=>{server.kill();throw error;});
}
const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true }).catch(error=>{server?.kill();throw error;});
const page = await browser.newPage();
const errors=[];
page.on('pageerror', error=>errors.push(error.message));
const clean=s=>s.replace(/[\u2066-\u2069]/g,'');
async function switchTo(language) {
  if(await page.locator('html').getAttribute('lang') !== language) await page.locator('.site-header .language-switcher').click();
  assert.equal(await page.locator('html').getAttribute('lang'),language);
  assert.equal(await page.locator('html').getAttribute('dir'),language==='ur'?'rtl':'ltr');
}
const allowed=/Directorate General of Immigration & Passports|Federal Board of Revenue|Provincial Administration \/ Deputy Commissioner Office|Police Khidmat Markaz \/ District Police|PakAssist|Pak Identity|WhatsApp|NADRA|CNIC|NICOP|FBR|NTN|PKR|Iris|Passport|(?:[a-z]+\.)*gov\.pk|PA-\d+|\bP\b|\bi\b/g;
async function audit(language, route) {
  const values=await page.evaluate(()=>{
    const out=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let node;
    while(node=walker.nextNode()) {
      const el=node.parentElement;
      if(!el||el.closest('script,style,.language-switcher,.logo')||!el.getClientRects().length) continue;
      if(node.textContent.trim())out.push(node.textContent.trim());
    }
    for(const el of document.querySelectorAll('[placeholder],[aria-label],[title]')) {
      if(el.closest('.language-switcher')||!el.getClientRects().length)continue;
      for(const attr of ['placeholder','aria-label','title'])if(el.hasAttribute(attr))out.push(el.getAttribute(attr));
    }
    return out;
  });
  const leaks=values.map(clean).filter(v=>language==='ur'?/[a-zA-Z]/.test(v.replace(allowed,'')):/[\u0600-\u06ff]/.test(v));
  assert.deepEqual(leaks,[],`${route} ${language} untranslated content`);
}
try {
  const slugs=['new-passport','passport-renewal','learner-driving-permit','cnic-registration','cnic-renewal','vehicle-transfer','fbr-income-tax','domicile-certificate','character-certificate'];
  const routes=['/','/services','/chat','/dashboard','/how-it-works','/about',...slugs.map(s=>'/services/'+s),'/services/missing'];
  for(const route of routes) {
    await page.goto(base+route);
    for(const language of ['en','ur','en','ur']) {await switchTo(language);await audit(language,route);}
  }
  await page.goto(base+'/services/cnic-renewal');
  await page.locator('.document-card').first().click();
  await switchTo('en'); assert.equal(await page.locator('.document-card.checked').count(),1);
  await switchTo('ur'); assert.equal(await page.locator('.document-card.checked').count(),1);
  await page.goto(base+'/services');
  await page.locator('.directory-search input').fill('پاسپورٹ');
  assert.equal(await page.locator('.service-card').count(),2);
  await page.locator('.directory-search input').fill('zzzz');await audit('ur','empty services');
  await page.goto(base+'/');
  await page.locator('.hero-search input').fill('شناختی');
  assert.ok(await page.locator('[role=option]').count()>0);await audit('ur','suggestions');
  await page.locator('.hero-search input').fill('zzzz');await audit('ur','empty suggestions');
  await page.goto(base+'/how-it-works');
  for(const button of await page.locator('.faqs button').all()) {
    await button.click();await audit('ur','FAQ');
    await switchTo('en');await audit('en','FAQ');await switchTo('ur');
  }
  await page.goto(base+'/dashboard');
  await page.locator('.appointment button').first().click();await audit('ur','notice');
  await switchTo('en');await audit('en','notice switch');
  await page.goto(base+'/chat');
  await page.locator('.followups button').first().click();await switchTo('ur');await audit('ur','chat followup');
  await page.locator('.chat-sidebar .primary-button').click();await audit('ur','chat empty');
  await page.locator('.chat-input input').fill('میرا سوال');await page.locator('.chat-input button').click();
  assert.ok((await page.locator('.message.user').last().innerText()).includes('میرا سوال'));
  await audit('ur','chat send');
  await page.reload();assert.equal(await page.locator('html').getAttribute('lang'),'ur');
  await page.setViewportSize({width:390,height:844});await page.goto(base+'/');
  await page.locator('.header-menu-toggle').click();await audit('ur','mobile menu');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'mobile horizontal overflow');
  fs.mkdirSync('.verification/screenshots',{recursive:true});
  await page.screenshot({path:'.verification/screenshots/urdu-home-mobile.png',fullPage:true});
  for(const route of routes) {
    await page.goto(base+route);await audit('ur',`mobile ${route}`);
  }
  assert.deepEqual(errors,[]);
  console.log(`PASS: ${routes.length} routes in both languages with repeated switches, search, FAQs, checklist persistence, dashboard notices, chat, reload and mobile menu.`);
} finally {await browser.close();server?.kill();}
