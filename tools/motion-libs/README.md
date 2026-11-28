# مكتبات الحركة (محفوظة محلياً)

الإنترنت لـ cdn.jsdelivr.net مسكر في الجلسات، فهني نسخ جاهزة. انسخ اللي تحتاجه جنب ملف index.html واربطه بـ `<script src="...">`.

| الملف | الأداة | الاستخدام | الرخصة |
|---|---|---|---|
| gsap.min.js | GSAP 3.15 | الحركة الأساسية والتايملاين | GSAP Standard (مجاني) |
| anime.umd.min.js | Anime.js 4 | حركات خفيفة ومتكررة (في HyperFrames: `autoplay:false` وادفعه لـ `window.__hfAnime`) | MIT |
| mo.umd.js | mo.js | انفجارات قلوب ونجوم للختام (اربطه بتايملاين GSAP عبر `setProgress`) | MIT |
| rough.js | Rough.js | ستايل رسم باليد (إطارات وأسهم) | MIT |

## خط الفيديو
1. التصميم: HTML + هالمكتبات، بألوان كوخ روزا.
2. التصوير لفيديو: `npx -y hyperframes@latest render -o out.mp4` (مهارة hyperframes في `.claude/skills/`).
3. قص الصمت من فيديو كلام: `pip install --break-system-packages auto-editor` ثم `auto-editor video.mp4`.
4. الدمج والصوت: ffmpeg (موجود في الجهاز).
