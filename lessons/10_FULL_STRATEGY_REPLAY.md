# Lesson 10 — Full Strategy Replay

ده أول درس نجمع فيه كل حاجة.

## الأدوات المطلوبة

```text
SPY 1m
SPY 5m
VWAP
ATR14 on 5m
Option chain only after signal
```

## Replay sequence

ممنوع نشوف المستقبل.

### Step A

عند:

```text
09:55 ET
```

حدد:

```text
ORH
ORL
```

### Step B

امشِ بار بخطوة لحد ما يظهر:

```text
5m close outside OR
```

أو اليوم يفضل من غير Break صالح.

### Step C

بعد Break:

احسب Retest band.

### Step D

راقب أول Retest صالح.

لو السعر خرج من الحد الخارجي:

```text
CANCELED
```

### Step E

استنى Confirmation.

### Step F

قبل Entry افحص Chop rule.

### Step G

لو صالح:

```text
Entry
Structural Stop
R
Target
```

### Step H

بعد تحديد الصفقة فقط، افتح Option Chain واختار العقد حسب V1.

## الأسئلة اللي هتجاوب عليها

```text
Is there a break?
Has retest started?
Did the retest fail?
Is confirmation complete?
Is the market CHOP by the frozen rule?
Trade / No Trade / Not Yet / Canceled?
```

## قاعدة التدريب

ممنوع تستخدم النتيجة اللاحقة لتبرير قرار سابق.
