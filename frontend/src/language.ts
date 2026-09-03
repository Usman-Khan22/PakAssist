const translations: Record<string, string> = {
  Home: 'ہوم', Services: 'خدمات', 'How It Works': 'یہ کیسے کام کرتا ہے', About: 'تعارف', 'Ask PakAssist': 'پاک اسسٹ سے پوچھیں',
  'Government services,': 'حکومتی خدمات،', 'made simple.': 'آسان بنا دی گئی ہیں۔', 'OFFICIAL CIVIC GUIDE': 'سرکاری شہری رہنما',
  'FIND YOUR WAY': 'اپنا راستہ تلاش کریں', 'Popular categories': 'مقبول شعبے', 'From question to confident action': 'سوال سے پُراعتماد اقدام تک',
  'THE SERVICE JOURNEY': 'خدمت کا سفر', 'Know what comes next': 'اگلا مرحلہ جانیں', 'MADE FOR EVERYONE': 'سب کے لیے',
  'OFFICIAL GATEWAYS': 'سرکاری ویب پورٹلز', 'Always close to the source': 'ہمیشہ اصل ذریعے کے قریب',
  'Your next step': 'آپ کا اگلا مرحلہ', 'YOUR NEXT STEP': 'آپ کا اگلا مرحلہ', 'Government Services': 'حکومتی خدمات',
  'Search services...': 'خدمات تلاش کریں...', 'All Services': 'تمام خدمات', Passport: 'پاسپورٹ', 'Driving License': 'ڈرائیونگ لائسنس',
  'CNIC/NADRA': 'شناختی کارڈ / نادرا', 'Vehicle Registration': 'گاڑی کی رجسٹریشن', 'Tax & Revenue': 'ٹیکس اور آمدنی', Documents: 'دستاویزات',
  Available: 'دستیاب', 'View guide': 'رہنما دیکھیں', 'Service not found': 'خدمت نہیں ملی', 'Return to services': 'خدمات پر واپس جائیں',
  'BEFORE YOU BEGIN': 'شروع کرنے سے پہلے', 'Eligibility checklist': 'اہلیت کی فہرست', 'PREPARE AHEAD': 'پہلے سے تیاری کریں',
  'Required documents': 'مطلوبہ دستاویزات', 'COSTS & TIMELINES': 'فیس اور مدت', 'Fee schedule': 'فیس کا شیڈول',
  'YOUR ROADMAP': 'آپ کا راستہ', 'Application process': 'درخواست کا عمل', 'Start online application': 'آن لائن درخواست شروع کریں',
  'Ask PakAssist AI': 'پاک اسسٹ اے آئی سے پوچھیں', 'New chat': 'نئی گفتگو', 'PINNED TOPICS': 'پن کیے گئے موضوعات',
  'RECENT CHATS': 'حالیہ گفتگو', TODAY: 'آج', YESTERDAY: 'کل', 'AI Agent Active': 'اے آئی ایجنٹ فعال',
  'Ask a follow-up question...': 'مزید سوال پوچھیں...', 'Attachments coming soon': 'منسلکات جلد دستیاب ہوں گے', 'Continue with': 'مزید جانیں:',
  'Normal or Urgent?': 'عام یا فوری؟', 'Adult or Minor?': 'بالغ یا نابالغ؟', 'Islamabad or Other City?': 'اسلام آباد یا کوئی اور شہر؟',
  'What can we help you navigate?': 'ہم آپ کی کیسے رہنمائی کر سکتے ہیں؟', 'Welcome back, Ahmed': 'خوش آمدید، احمد',
  'Active Applications': 'فعال درخواستیں', 'Documents Prepared': 'تیار دستاویزات', 'Upcoming Appointment': 'آئندہ ملاقات',
  'Your applications': 'آپ کی درخواستیں', 'View all': 'سب دیکھیں', 'IN PROGRESS': 'جاری ہے', 'DOCUMENT CHECKLIST': 'دستاویزات کی فہرست',
  'NEXT APPOINTMENT': 'اگلی ملاقات', 'QUICK ACTIONS': 'فوری اقدامات', Reschedule: 'دوبارہ وقت لیں', Cancel: 'منسوخ کریں',
  'STEP-BY-STEP SYSTEM': 'مرحلہ وار نظام', 'How PakAssist Works': 'پاک اسسٹ کیسے کام کرتا ہے', 'CORE FUNCTIONS': 'بنیادی سہولیات',
  'Everything you need to move forward': 'آگے بڑھنے کے لیے ہر ضروری چیز', 'TRANSPARENCY NOTICE': 'شفافیت کا نوٹس', 'COMMON QUESTIONS': 'عام سوالات',
  'Good to know': 'جاننا مفید ہے', 'OUR IDENTITY': 'ہماری شناخت', 'About PakAssist': 'پاک اسسٹ کے بارے میں', 'THE MISSION': 'مقصد',
  'Civic tasks shouldn’t feel like detective work.': 'شہری کام جاسوسی جیسے مشکل نہیں ہونے چاہئیں۔', 'WHAT GUIDES US': 'ہماری رہنمائی کے اصول',
  'Useful first. Always honest.': 'سب سے پہلے مفید، ہمیشہ ایماندار۔', 'CIVIC ROADMAP': 'شہری منصوبہ', 'Growing with the people we serve.': 'لوگوں کے ساتھ آگے بڑھنا۔',
  'Built by Citizens,': 'شہریوں کا بنایا ہوا،', 'For Citizens.': 'شہریوں کے لیے۔', 'OPEN-SOURCE CIVIC TECHNOLOGY': 'اوپن سورس شہری ٹیکنالوجی',
  'New Passport Application': 'نئے پاسپورٹ کی درخواست', 'Passport Renewal': 'پاسپورٹ کی تجدید', "Learner's Driving Permit": 'لرنر ڈرائیونگ پرمٹ',
  'CNIC Registration': 'شناختی کارڈ کا اندراج', 'CNIC Renewal': 'شناختی کارڈ کی تجدید', 'Biometric Vehicle Transfer': 'بائیومیٹرک گاڑی منتقلی',
  'FBR Income Tax Filing': 'ایف بی آر انکم ٹیکس فائلنگ', 'Domicile Certificate': 'ڈومیسائل سرٹیفکیٹ', 'Police Character Certificate': 'پولیس کریکٹر سرٹیفکیٹ',
  'Original CNIC': 'اصل شناختی کارڈ', 'Recent photograph': 'حالیہ تصویر', 'Proof of address': 'پتے کا ثبوت', 'Previous passport': 'پچھلا پاسپورٹ',
  Normal: 'عام', Urgent: 'فوری', 'Fast Track': 'فاسٹ ٹریک', Completed: 'مکمل', 'In Progress': 'جاری ہے', 'Under Review': 'جائزے کے تحت',
  'Tap to mark ready': 'تیار ہونے پر نشان لگائیں', Ready: 'تیار',
};
const reverse = new Map(Object.entries(translations).map(([english, urdu]) => [urdu, english]));
let observer: MutationObserver | undefined;
function translateNode(root: Node, urdu: boolean) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  let node: Node | null;
  while ((node = walker.nextNode())) nodes.push(node as Text);
  nodes.forEach(textNode => {
    const value = textNode.nodeValue?.trim();
    if (!value || value.length > 180) return;
    const translated = urdu ? translations[value] : reverse.get(value);
    if (translated) textNode.nodeValue = textNode.nodeValue!.replace(value, translated);
  });
  const elementRoot = root as Element;
  elementRoot.querySelectorAll('input[placeholder], textarea[placeholder]').forEach((element: Element) => {
    const input = element as HTMLInputElement;
    const value = urdu ? translations[input.placeholder] : reverse.get(input.placeholder);
    if (value) input.placeholder = value;
  });
}
export function applyLanguage(urdu: boolean) {
  document.documentElement.lang = urdu ? 'ur' : 'en';
  document.documentElement.dir = urdu ? 'rtl' : 'ltr';
  document.body.classList.toggle('urdu-mode', urdu);
  if (observer) observer.disconnect();
  translateNode(document.body, urdu);
  observer = new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(node => translateNode(node, urdu))));
  observer.observe(document.body, { childList: true, subtree: true });
}
export function getStoredLanguage() { return localStorage.getItem('pakassist-language') === 'ur'; }
export function setStoredLanguage(urdu: boolean) { localStorage.setItem('pakassist-language', urdu ? 'ur' : 'en'); applyLanguage(urdu); }
