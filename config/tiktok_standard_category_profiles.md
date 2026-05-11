# TikTok Shop 标准品类配置

> 基于 API 查询结果整理,涵盖女装与女士内衣、休闲与运动两大类目

## 一、全局默认值

```json
{
  "brand": "No Brand",
  "condition": "NEW",
  "currency": "USD",
  "category_version": "v2",
  "listing_platform": "TIKTOK_SHOP",
  "exchange_rate_cny_to_usd": 0.14,
  "warehouse_id": "7637357976526718738",
  "package_unit": "CENTIMETER",
  "weight_unit": "GRAM",
  "default_package": {"length": "23", "width": "22", "height": "6", "unit": "CENTIMETER"},
  "default_weight": {"value": "200", "unit": "GRAM"}
}
```

## 二、大类一：女装与女士内衣

### 2.1 连衣裙/裙装

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Casual Dresses | 601281 | Y |
| Dresses | 814600 | Y |
| Evening Dresses | 906000 | Y |
| Party Dresses | 905872 | Y |
| Business Dresses | 906128 | Y |
| Bridesmaid Dresses | 961672 | Y |
| Wedding Guest Dresses | 905616 | Y |
| Formal Dresses | 1198992 | Y |
| Swimdresses | 847120 | Y |
| Skirts | 601264 | Y |
| Jumpsuits & Rompers | 902800 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(仅当 pcs 不一致时)

**关键销售属性(来自TikTok API):**
1. Materials - Polyester, Cotton, Linen, Silk, Nylon
2. Season - Spring, Summer, Autumn, Winter, All Seasons
3. Style - Elegant, Minimalist, Sexy, Basic, Party, Holiday, Chic
4. Dress Length - Knee Length, Above Knee, Maxi, Midi, Mini
5. Country of origin - China, USA, Vietnam, Korea
6. Sleeve Length - Short Sleeve, Long Sleeve, Sleeveless, Half Sleeve
7. Neckline - Round Neck, V Neck, Sweetheart, High Neck, Deep V Neck
8. Closure Type - Pull On, Tie, Zipper, Button
9. Sleeve Type - Flutter, Flare, Bishop, Drop Shoulder, Regular
10. Pattern - Solid, Floral, Striped, Plaid, Colorblock, Graphic
11. Clothing Type - Straight, A-Line, Fit & Flare, Bodycon, Wrap
12. Embellishment - Fringe, Sequins, Bow, Lace, Buttons, None

### 2.2 上衣(T恤/衬衫/吊带)

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Women's T-shirts | 601302 | Y |
| Blouses & Shirts | 601265 | Y |
| Shirts & Blouses | 601314 | Y |
| Women's Tanks & Camis | 843400 | Y |
| Polo Shirts | 960776 | Y |
| Bodysuits | 843528 | Y |
| Koko & Tops | 601326 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Polyester, Linen, Silk, Nylon
2. Season - Spring, Summer, Autumn, All Seasons
3. Style - Minimalist, Basic, Sexy, Street, Fashion, Holiday
4. Country of origin - China, USA, Vietnam
5. Sleeve Length - Short, Long, Sleeveless, Half Sleeve
6. Neckline - Round Neck, V Neck, Sweetheart, High Neck, Cowl
7. Closure Type - Pull On, Button, Zipper, Tie
8. Sleeve Type - Flutter, Flare, Bishop, Raglan, Regular, Drop Shoulder
9. Pattern - Solid, Floral, Striped, Plaid, Graphic, Colorblock
10. Fit - Regular, Slim, Loose, Oversized
11. Top Length - Regular, Long, Cropped, Tunic

### 2.3 裤子/短裤

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Pants | 601277 | Y |
| Shorts | 601266 | Y |
| Jeans | 601276 | Y |
| Leggings | 601274 | Y |
| Overalls | 902672 | Y |
| Overalls Shorts | 902544 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Denim, Polyester, Linen, Nylon
2. Season - Spring, Summer, Autumn, All Seasons
3. Style - Basic, Street, Minimalist, Fashion, Sporty
4. Waist Height - High Waist, Mid Waist, Low Waist
5. Hem Length - Full Length, Ankle, Cropped, Short
6. Pattern - Solid, Striped, Plaid, Colorblock, Camouflage
7. Fit - Regular, Slim, Loose, Skinny
8. Closure Type - Zipper, Button, Pull On, Drawstring
9. Inseam Style - Straight, Flared, Bootcut, Skinny, Wide Leg

### 2.4 内衣/内裤/文胸

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Sports Bras | 603729 | Y |
| Everyday Bras | 899472 | Y |
| Bralettes | 845576 | Y |
| Strapless Bras | 899344 | Y |
| Adhesive Bras | 899600 | Y |
| Briefs | 898448 | Y |
| Thongs | 897936 | Y |
| Underwear Sets | 845704 | Y |
| Shapewear Bodysuit | 897424 | Y |
| Period Panties | 898064 | Y |
| Maternity Underwear | 700710 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Lace, Polyester, Nylon, Spandex
2. Style - Minimalist, Sexy, Basic, Sporty, Fashion
3. Country of origin - China, USA
4. Bra Type - Push Up, Wireless, Balconette, Sports
5. Strap Type - Adjustable, Convertible, Racerback, Spaghetti
6. Neckline - Plunge, V Neck, Scoop, High Neck
7. Closure Type - Front Close, Back Close, Pull On
8. Pattern - Solid, Lace, Floral, Printed
9. Panties Style - Brief, Thong, Hipster, Bikini, Boyshort

### 2.5 睡衣/家居服

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Pajama Sets | 1197840 | Y |
| Nightdresses | 846088 | Y |
| Nightshirts | 842120 | Y |
| Bathrobes & Dressing Gowns | 845960 | Y |
| Loungewear Sets | 905104 | Y |
| Loungewear Dresses | 905360 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Polyester, Silk, Flannel, Satin
2. Season - Spring, Summer, Autumn, All Seasons
3. Style - Minimalist, Sexy, Cute, Basic, Fashion
4. Country of origin - China, USA
5. Sleeve Length - Short, Long, Sleeveless
6. Neckline - Round Neck, V Neck, Collar
7. Pattern - Solid, Floral, Striped, Cartoon
8. Fit - Regular, Loose, Oversized

### 2.6 泳衣/泳装

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Women's One-Pieces | 1037584 | Y |
| Bikinis Set | 1038224 | Y |
| Women's Tankinis Set | 1036560 | Y |
| Women's Long-sleeve Rashguard| 1649168 | Y |
| Women's Short-sleeve Rashguard| 1649040 | Y |
| Islamic Swimwear | 601347 | Y |
| Cover Ups | 847376 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Nylon, Polyester, Spandex, Cotton
2. Washing Instructions - Machine Wash, Hand Wash, Cold Wash
3. Weaving Method - Knitting, Woven, Crochet
4. Swimwear Type - One-Piece, Bikini, Tankini, Rashguard
5. Sports Feature - UV Protection, Quick Dry, Chlorine Resistant
6. Pattern - Solid, Floral, Striped, Leopard, Graphic
7. Country of origin - China, USA
8. Season - Summer, All Seasons

### 2.7 外套/开衫/卫衣

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Women's Hoodies | 901776 | Y |
| Women's Cardigans | 900624 | Y |
| Women's Pullover Sweatshirts | 901648 | Y |
| Women's Casual Jackets | 900752 | Y |
| Women's Lightweight Jackets | 901264 | Y |
| Women's Fleece Jackets | 901392 | Y |
| Women's Down Jacket | 901520 | Y |
| Women's Trench & Rain Jacket | 900880 | Y |
| Vests | 960648 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Polyester, Denim, Leather, Fleece
2. Season - Spring, Autumn, Winter, All Seasons
3. Style - Basic, Street, Minimalist, Sporty, Fashion
4. Country of origin - China, USA, Vietnam
5. Sleeve Length - Long, Short, Sleeveless
6. Neckline - Round Neck, V Neck, Hooded, Collar
7. Closure Type - Zipper, Button, Pull On, Snap
8. Pattern - Solid, Colorblock, Striped, Plaid
9. Fit - Regular, Slim, Loose, Oversized
10. Collar Type - Stand Collar, Hooded, Lapel, Peter Pan

## 三、大类二：休闲与运动

### 3.1 运动裤/紧身裤

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Leggings | 601274 | Y |
| Women's Sports Leggings | 1074064 | Y |
| Leg Shaping Shorts | 897680 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Nylon, Polyester, Spandex, Cotton
2. Pattern - Solid, Camouflage, Colorblock, Striped
3. Season - Spring, Summer, Autumn, All Seasons
4. Style - Sporty, Basic, Fashion, Minimalist
5. Waist Height - High Waist, Mid Waist
6. Fit - Regular, Slim, Compression
7. Sports Feature - Moisture Wicking, Compression, Quick Dry
8. Hem Length - Full, Ankle, Cropped, Short
9. Leg Style - Straight, Skinny, Flared

### 3.2 运动上衣

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Women's Sports Hoodie | 1070736 | Y |
| Women's Sports Sweatshirt | 1070352 | Y |
| Women's Sports Singlet | 1070480 | Y |
| Women's Sports Vest | 1070096 | Y |
| Women's Short Sleeves Sport T-Shirt | 1678352 | Y |
| Women's Long Sleeves Sport T-Shirt | 1678480 | Y |
| Sports Bras | 603729 | Y |
| Hoodies | 1154448 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Materials - Cotton, Polyester, Mesh, Spandex
2. Pattern - Solid, Colorblock, Camouflage, Striped
3. Season - Spring, Summer, Autumn, All Seasons
4. Style - Sporty, Basic, Fashion, Minimalist
5. Country of origin - China, USA
6. Sleeve Length - Short, Long, Sleeveless
7. Fit - Regular, Slim, Loose
8. Sports Feature - Moisture Wicking, Quick Dry, Breathable

### 3.3 运动短裤/套装

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Women's Sports Shorts | 1072016 | Y |
| Women's Sportswear Set | 1073168 | Y |
| Shorts | 601266 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Pattern - Solid, Colorblock, Striped
2. Season - Spring, Summer, All Seasons
3. Style - Sporty, Basic, Fashion
4. Material - Cotton, Polyester, Mesh
5. Fit - Regular, Slim, Loose

### 3.4 袜子

| 子类目 | API ID | 叶子节点 |
|---|---|---|
| Socks | 601346 | Y |
| Ankle Socks | 896912 | Y |
| Low Cut Socks | 896528 | Y |
| Mid-Calf Socks | 896400 | Y |
| Knee-High Socks | 896656 | Y |
| Over-The-Calf Socks | 896144 | Y |
| No Show & Liner Socks | 896272 | Y |
| Thermal Underwear Sets | 895888 | Y |

**变体属性:** Size(必需), Color(可选), Qty/pack(条件)

**关键销售属性:**
1. Sock Height - Ankle, Crew, Knee-High, Over-the-Calf
2. Pattern - Solid, Striped, Colorblock, Cartoon
3. Season - Spring, Summer, Autumn, Winter, All Seasons
4. Style - Basic, Fashion, Sporty, Cute
5. Material - Cotton, Polyester, Nylon, Wool
6. Toe Style - Closed Toe, Open Toe, Reinforced
7. Socks Type - Casual, Athletic, Dress, Thermal
8. Sheer - Opaque, Semi-Opaque, Sheer

## 四、标准输入表格格式

| 列名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parent_sku | text | Y | 父商品 ID |
| child_sku | text | Y | 子 SKU |
| title_en | text | Y | 英文标题 |
| description_en | text | Y | 英文描述(HTML) |
| category_id | text | Y | 叶子类目 ID |
| category_name | text | - | 类目名(辅助) |
| price_cny | number | Y | 采购价(CNY) |
| price_usd | number | - | 售价(USD),优先于 price_cny |
| stock | integer | Y | 库存量 |
| size | text | Y | 尺码(S/M/L/XL/2XL) |
| color | text | - | 颜色 |
| pcs | integer | - | 件数,不填默认为 1 |
| image_url | url | Y | 商品图片 URL |
| weight_g | number | - | 重量(g) |
| length_cm | number | - | 包装长(cm) |
| width_cm | number | - | 包装宽(cm) |
| height_cm | number | - | 包装高(cm) |
| pattern | text | - | 销售属性:图案 |
| season | text | - | 销售属性:季节 |
| material | text | - | 销售属性:材质 |
