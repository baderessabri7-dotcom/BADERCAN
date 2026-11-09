# موقع قناة Rili's World — بدر

| الملف | ما هو |
|---|---|
| `index.html` | الموقع نفسه |
| `admin.html` | **لوحة التحكم الخاصة بك** — منها تضيف الفيديوهات والروابط وكل شيء، بدون تعديل كود |

---

## 🛠️ لوحة التحكم (admin.html)
افتح `https://<موقعك>/rili/admin.html` وسجّل الدخول بحساب Google. فيها:
- **📺 الفيديوهات**: إضافة/تعديل/حذف. الصق رابط يوتيوب ← الصورة المصغّرة تظهر تلقائيًا. رابط تيك توك، الملخص، النقاط، الفصول.
- **🔗 الروابط والدعم**: روابط حساباتك وروابط الدعم المادي.
- **🗳️ أفكار التصويت**، **❓ الاختبار**، **💡 معلومات رائد الفضاء**، **⚙️ عام** (النبذة، الأرقام، إيميل الاقتراحات).

اضغط **«حفظ ونشر»** ← التغييرات تظهر في الموقع فورًا.

### إعداد لمرة واحدة فقط (في Firebase Console لمشروع `rili-s-world-6b67e`)
1. **Authentication → Get started → Sign-in method → Google → Enable → Save**
2. **Authentication → Settings → Authorized domains → Add domain** وأضف نطاق موقعك (مثلًا `username.github.io`).
3. **Firestore Database → Rules** وأضف داخل `match /databases/{database}/documents { ... }` (بدّل الإيميل بإيميلك أنت):
```
match /rili_site/{doc} {
  allow read: if true;
  allow write: if request.auth != null && request.auth.token.email == "ضع_إيميلك_هنا@gmail.com";
}
match /rili_votes/{id} {
  allow read: if true;
  allow create: if request.resource.data.keys().hasOnly(['votes']) && request.resource.data.votes == 1;
  allow update: if request.resource.data.keys().hasOnly(['votes']) && request.resource.data.votes == resource.data.votes + 1;
}
```
ثم **Publish**. الآن أنت وحدك تقدر تعدّل، والزوار يقرؤون ويصوّتون فقط.

> أول مرة تفتح اللوحة تظهر القيم الافتراضية الموجودة في الموقع — اضغط «حفظ ونشر» مرة واحدة لتفعيلها.

---

## النشر مجانًا
GitHub → Settings → Pages → اختر الفرع → الموقع يصير على `https://<username>.github.io/BADERCAN/rili/`
ولوحة التحكم على `https://<username>.github.io/BADERCAN/rili/admin.html`

## ملاحظات
- **اقتراحات الناس** من النموذج توصلك أنت فقط (إيميل، أو Formspree إذا وضعت رابطه في «عام»). ما تظهر للعامة.
- **الخطوط** (Cairo وFredoka) مضمّنة داخل `index.html` فتظهر صح حتى بدون إنترنت.
- إذا ما قدر الموقع يتصل بقاعدة البيانات، يعرض القيم المكتوبة داخل `index.html` تلقائيًا.
