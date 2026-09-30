# Lesson 03 — Retest, Confirmation, and Invalidation

ده قلب الاستراتيجية.

## الفكرة

بعد الكسر مش بنجري ورا السعر.

نستنى السعر يرجع ناحية المستوى المكسور ونشوف هل المستوى هيمسك ولا لأ.

## Retest Band

المنطقة مش خط مقدس.

للكول:

```text
ORH ± 0.25 × ATR5
```

للبوت:

```text
ORL ± 0.25 × ATR5
```

## CALL Retest

لازم أول Retest صالح بعد شمعة الكسر يعمل:

```text
Low داخل المنطقة
Close ≥ ORH
```

مسموح wick بسيط تحت ORH.

لكن لو الـ wick خرج تحت الحد السفلي للمنطقة:

```text
CANCEL
```

مش نستنى Retest أحسن بعدين.

## Confirmation

بعد Retest، لسه ما دخلناش.

نستنى شمعة دقيقة لاحقة تقفل فوق High بتاع Retest bar.

```text
Retest
→ Hold
→ Confirmation
→ Entry next 1m bar
```

للبوت العكس.

## Structural Stop

الكول:

```text
أقل Low من بداية الـ Retest لحد Confirmation
```

البوت:

```text
أعلى High من بداية الـ Retest لحد Confirmation
```

## Invalidation

النسخة الحالية مش بتخرج بسبب wick فقط.

```text
CALL:
1m close < structural stop

PUT:
1m close > structural stop
```

## أربع حالات لازم تعرف تفرق بينهم

```text
Clean Retest
Wick-Allowed Retest
Failed Deep Retest
No Retest
```

## أهم غلطة

تشوف الحركة بعد ما طلعت وتختار أي شمعة قديمة وتسميها Retest.

عشان كده النظام بيحدد:

```text
first qualifying retest bar
```

قبل ما نعرف النتيجة.
