# موقع قناة Rili — بدر

ملف واحد: `index.html` (بدون أي مكتبات أو سيرفر).

## كيف أعدّل الموقع؟
افتح `index.html` وابحث عن:

- **`const SITE`** ← اسم القناة، النبذة، الأرقام، روابط التواصل، روابط الدعم، وإعدادات نموذج الاقتراحات.
- **`const VIDEOS`** ← قائمة الفيديوهات. انسخ أي فيديو والصقه وعدّل: العنوان، التاريخ، المدة، التصنيف، الملخص، أهم النقاط، الفصول.
  - `youtubeId`: الكود اللي بعد `v=` في رابط يوتيوب — إذا حطيته تظهر صورة الفيديو ويشتغل داخل الموقع.
  - إذا ما فيه `youtubeId` تظهر صورة مرسومة بستايل القناة (`art`: galaxy / moon / nebula / planet).

## الاقتراحات
- سجّل في https://formspree.io (مجاني) وأنشئ نموذج، وحط رابطه في `formEndpoint` — توصلك الاقتراحات على الإيميل.
- إذا تركته فاضي، الزر يفتح تطبيق الإيميل عند الزائر ويرسل إلى `requestEmail`.

## النشر مجاناً
GitHub → Settings → Pages → اختر الفرع → يصير الموقع على:
`https://<username>.github.io/BADERCAN/rili/`

## لوحة التصويت على الأفكار (Firebase)
الموقع يستخدم مشروع Firebase الخاص بك `badercan-63e2a` (نفس مشروع الصفحة الثانية)، في مجموعة منفصلة اسمها `rili_ideas`.

1. افتح Firebase Console → Firestore Database → Rules، وأضف هذه القواعد (بدون حذف قواعدك الحالية):
```
match /rili_ideas/{id} {
  allow read: if true;
  allow create: if request.resource.data.votes == 0
    && request.resource.data.title is string && request.resource.data.title.size() <= 120
    && request.resource.data.details is string && request.resource.data.details.size() <= 1500;
  allow update: if request.resource.data.diff(resource.data).affectedKeys().hasOnly(['votes'])
    && request.resource.data.votes == resource.data.votes + 1;
}
```
2. لإخفاء فكرة غير مناسبة: افتحها في Firestore وغيّر `hidden` إلى `true`.
3. إذا الاتصال فشل، اللوحة تشتغل على جهاز الزائر فقط وتكتب ملاحظة بذلك.
4. حساب/إيميل صاحب الاقتراح **لا يُحفظ** في اللوحة العامة؛ يوصلك فقط إذا ضبطت `formEndpoint`.

## الاختبار
اكتب أسئلتك في `const QUIZ` داخل `index.html`. كل سؤال بهذا الشكل:
```js
{ q:"ما أكبر كوكب في المجموعة الشمسية؟", a:["زحل","المشتري","الأرض","نبتون"], correct:2, why:"المشتري يتسع لأكثر من 1300 أرض." },
```
- `correct` رقم الخيار الصحيح (1 = الأول).
- الأسئلة تظهر بنفس ترتيبك. إذا القائمة فاضية، قسم الاختبار يختفي من الموقع.
