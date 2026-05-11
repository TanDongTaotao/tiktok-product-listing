# LLM Content Generation Template

Reference for generating English titles and descriptions for TikTok Shop products.
Loaded by the agent when processing Sub-Skill 1 (Task B).

---

## Title Format

**Pipe-separated SEO keyword phrases.** Max 255 characters, English only.

Pattern: `[Core Product Phrase] | [Alternative Keyword Variation] | [Occasion/Style Phrase]`

| Chinese Name | English Title |
|---|---|
| 纯色圆领长袖叶边连衣裙 | Solid Round Neck Long Sleeve Dress | Leaf Hem A-Line Midi Dress | Elegant Casual Daily Wear Dress |
| 镂空连体泳衣 | Women's Hollow Out One Piece Swimsuit | Cutout Monokini Bathing Suit | Sexy Beach Pool Swimwear |
| 性感辣妹长袖修身V领蕾丝上衣 | Sexy Long Sleeve Fitted V Neck Lace Top | Slim Fit Going Out Blouse | Elegant Date Night Clubwear Top |
| 高腰紧身运动裤 | High Waist Compression Leggings | Workout Yoga Pants for Women | Gym Fitness Running Tights |
| 短款开衫毛衣 | Women's Cropped Cardigan Sweater | Open Front Knit Shrug | Elegant Layering Piece Casual Chic |
| 蕾丝吊带睡裙 | Women's Lace Camisole Sleep Dress | Spaghetti Strap Chemise Nightgown | Comfortable Lingerie Lounge Sleepwear |
| 深V网纱收腰连衣裙 | Women's Deep V Mesh Waist Mini Dress | Flared Bell Sleeve Bodycon Dress | Sexy Evening Party Clubwear |
| 露背绑带镂空罩衫 | Women's Backless Tie Knit Cover Up | Crochet Beach Swimsuit Cover Up | Boho Open Knit Resort Wear |

Rules:
- Each pipe segment targets a different search intent
- Include product type, material, fit, style, occasion keywords
- Do NOT invent features not implied by source data
- Strip ALL Chinese characters

---

## Description Format

HTML format, English only. Structured with emoji headers. Minimum ~500 characters.

**Required sections:**

```
<p>Opening elevator pitch (1-2 sentences)</p>

✨ Key Features:
• Feature Name — Benefit description
• Feature Name — Benefit description
• Feature Name — Benefit description
• Feature Name — Benefit description

🖤 Style Tips: How to wear and what to pair with

📅 Occasions: Where to wear

📦 Available in multiple sizes — Please refer to the size chart before ordering to ensure the best fit.
```

**Full example — 纯色圆领长袖叶边连衣裙 (Solid Round Neck Dress):**

```html
<p>Elevate your wardrobe with this elegant solid round-neck long-sleeve dress, featuring a unique leaf-hem design. Perfect for transitioning from office to evening with effortless sophistication.</p>

✨ Key Features:
• Round Neckline — Classic, versatile cut that frames the face beautifully
• Long Sleeves — Full coverage with a sleek, polished look suitable for any season
• Leaf-Hem Detail — Unique scalloped hem adds a feminine, romantic touch
• A-Line Silhouette — Universally flattering shape that skims the body without clinging
• Soft Breathable Fabric — Comfortable all-day wear with a smooth drape

🖤 Style Tips: Tuck into knee-high boots with a leather jacket for fall, or wear with pointed-toe heels and delicate jewelry for a dinner date.

📅 Occasions: Office Wear | Casual Daily | Date Night | Brunch | Weekend Outings

📦 Available in multiple sizes — Please refer to the size chart before ordering to ensure the best fit.
```

**Full example — 镂空连体泳衣 (Hollow-Out One Piece Swimsuit):**

```html
<p>Turn heads at the beach with this stunning hollow-out one-piece swimsuit, designed for women who want to make a statement. The cutout detailing and flattering silhouette combine sexy style with comfortable wear.</p>

✨ Key Features:
• Hollow-Out Cutout Design — Strategic cutouts create a bold, eye-catching look while maintaining support
• Quick-Dry Fabric — Lightweight, breathable material keeps you comfortable from pool to lounger
• Flattering One-Piece Silhouette — Body-hugging fit that smooths and shapes without restricting movement
• Adjustable Straps — Customize your fit for all-day comfort and confidence

🖤 Style Tips: Pair with a sheer cover-up, oversized sunglasses, and strappy sandals for a complete beach-to-bar look.

📅 Occasions: Beach Vacation | Pool Party | Resort Wear | Honeymoon | Summer Cruise

📦 Available in multiple sizes — Please refer to the size chart before ordering to ensure the best fit.
```

**Additional real-world example — 女式运动文胸 (Women's Sports Bra):**

```html
<p>Designed for performance and comfort, this supportive sports bra features a racerback design and moisture-wicking fabric. Perfect for medium-impact workouts, yoga, and everyday training.</p>

✨ Key Features:
• Racerback Design — Allows full range of motion while providing secure support
• Moisture-Wicking Fabric — Keeps you dry and comfortable throughout your workout
• Removable Padding — Customize your coverage and shape
• Wide Bottom Band — Stays in place without riding up during movement

Material & Comfort:
• Soft, breathable blend of nylon and spandex
• Four-way stretch for unrestricted movement
• Flatlock seams to prevent chafing

🖤 Style Tips: Pair with high-waist leggings and a zip-up hoodie for a complete gym look. Layer under a tank top for extra coverage.

📅 Occasions: Gym | Yoga | Pilates | Running | HIIT | Dance | Everyday Wear

📦 Available in multiple sizes — Please refer to the size chart before ordering to ensure the best fit.
```

---

## Rules Summary

1. Base ALL features on actual product data — never invent
2. Each feature bullet: `• Name — Benefit description`
3. Include SEO keywords naturally throughout
4. Minimum ~500 characters of substantive content
5. End every description with the size chart note
6. Strip ALL Chinese characters from title and description
