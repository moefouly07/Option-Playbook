# Lesson 08 — Execution, Spread, and Slippage

دي من أهم دروس السكالب.

## Bid

السعر اللي المشتري عارضه.

## Ask

السعر اللي البائع طالبُه.

## Spread

```text
Spread = Ask − Bid
```

مثال:

```text
Bid = 1.00
Ask = 1.10
Spread = 0.10
```

لو اشتريت فورًا على Ask وبعت فورًا على Bid، عندك احتكاك كبير حتى لو الأصل ما اتحركش.

## V1 conservative accounting

من غير Fill حقيقي:

```text
Buy = ASK
Sell = BID
```

مش:

```text
Mark
Mid
Last
```

## Slippage

لو كنت متوقع تشتري:

```text
1.10
```

واتنفذت:

```text
1.13
```

الفرق Slippage.

## Market Order

ممكن يتنفذ بسرعة، لكن السعر غير مضمون.

## Limit Order

بتحدد أقصى سعر شراء أو أقل سعر بيع تقبله، لكن التنفيذ نفسه مش مضمون.

## ليه الموضوع حساس للسكالب؟

لو هدف الحركة صغير، كام سنت Spread وSlippage ممكن ياكلوا نسبة كبيرة من الربح المتوقع.

عشان كده في الاختبار هنفصل:

```text
Underlying edge
Option friction
```

## قاعدة عملية

ما تبصش على:

```text
Last price
```

لوحده وتعتبره السعر اللي هتقدر تدخل أو تخرج عليه.
